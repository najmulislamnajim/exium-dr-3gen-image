import os
import zipfile
import shutil
import openpyxl
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from .models import Territory, ThreeGenImage
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .utils import get_img_obj, render_upload_preview
from django.db.models import Q
from django.core.paginator import Paginator

def home(request):
    return redirect('login')

def login_view(request):
    """
    Handle user login with territory code or admin credentials.
    """
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('upload_preview')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to upload_preview if not superuser
            if not user.is_superuser:
                messages.success(request, "Login successful.")
                return redirect('upload_preview')
            # Redirect superuser to territory_list
            messages.success(request, "Login successful.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    return render(request, 'login/login.html')


@login_required
def user_logout(request):
    """
    Log out the current user and redirect to login page.
    """
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def upload_preview(request):
    """
    Display a preview of upload form for the current user's territory.
    """
    if request.user.is_superuser:
        return redirect('territory_list')
    territory = request.user.username
    obj=Territory.objects.get(territory=territory)
    img_obj= ThreeGenImage.objects.filter(territory__territory=territory)
    count = img_obj.count()
    return render(request, 'core/upload-preview.html', {'obj':obj, 'img_obj':img_obj, 'count':count})

@login_required
def upload(request, instance_id):
    """
    View to handle uploading three generation images for a doctor.
    
    Args:
        request (HttpRequest): The HTTP request object.
        instance_id (int): The instance ID for the doctor (e.g., 1 or 2).
        
    Returns:
        HttpResponse: The HTTP response object, render upload template.
    """
    if request.method == 'POST':
        try:
            if request.user.is_superuser:
                territory_id = int(request.POST.get('territory'))
            else:
                territory_id = int(request.user.username)
            dr_rpl_id = request.POST.get('dr_rpl_id')
            dr_name = request.POST.get('dr_name')
            dr_image = request.FILES.get('dr_image')
            dr_parents_image = request.FILES.get('dr_parents_image')
            dr_children_image = request.FILES.get('dr_children_image')
            
            # Get the Territory instance
            try:
                print('territory id is', territory_id)
                territory = Territory.objects.get(territory=territory_id)
            except Territory.DoesNotExist:
                messages.error(request, "Invalid Territory selected.")
                return redirect('upload', instance_id=instance_id)
            
            try:
                img_obj = ThreeGenImage.objects.get(territory=territory, instance_id=instance_id)
                old_folder_name = f"{img_obj.dr_rpl_id} - {img_obj.dr_name}"

                zone = territory.zone_name
                region = territory.region_name
                old_folder_path = os.path.join(settings.MEDIA_ROOT, 'dr_images', zone, region, str(territory_id), old_folder_name)
                
                # Update data only if provided
                if dr_rpl_id:
                    img_obj.dr_rpl_id = dr_rpl_id
                if dr_name:
                    img_obj.dr_name = dr_name
                if dr_image:
                    print('uploaded dr image')
                    img_obj.dr_image = dr_image
                if dr_parents_image:
                    img_obj.dr_parents_image = dr_parents_image
                if dr_children_image:
                    img_obj.dr_children_image = dr_children_image
                    
                new_folder_name = f"{img_obj.dr_rpl_id} - {img_obj.dr_name}"
                
            except ThreeGenImage.DoesNotExist:
                # Validate required fields
                if not (dr_rpl_id and dr_name):
                    messages.error(request, "Doctor RPL ID and Doctor Name are required.")
                    return redirect('upload', instance_id=instance_id)

                if not (dr_image and dr_parents_image and dr_children_image):
                    messages.error(request, "All three images are required.")
                    return redirect('upload', instance_id=instance_id)
                
                img_obj = ThreeGenImage(
                    territory=territory,
                    instance_id=instance_id,
                    dr_rpl_id=dr_rpl_id,
                    dr_name=dr_name,
                    dr_image=dr_image,
                    dr_parents_image=dr_parents_image,
                    dr_children_image=dr_children_image
                )
                
                old_folder_path = None
                old_folder_name = None
                new_folder_name = f"{dr_rpl_id} - {dr_name}"
            
            # Validate and Save
            try:
                img_obj.full_clean()
                img_obj.save()
                
                # Delete old folder if name changed
                if old_folder_path and old_folder_name != new_folder_name and os.path.exists(old_folder_path):
                    shutil.rmtree(old_folder_path)
                messages.success(request, f"Images for {dr_name} (RPL ID: {dr_rpl_id}) uploaded successfully.")
                if request.user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('doctor_view', instance_id=instance_id)
            except ValidationError as e:
                error_messages = []
                if isinstance(e.message_dict, dict):
                    # Check for unique constraint on dr_rpl_id
                    if 'dr_rpl_id' in e.message_dict:
                        error_messages.append(f"Doctor RPL ID '{dr_rpl_id}' already exists.")
                    # Check for custom validation error for two-doctor limit
                    if '__all__' in e.message_dict and any(
                        "maximum of two doctors" in msg.lower() for msg in e.message_dict['__all__']
                    ):
                        error_messages.append("This territory already has two doctor images.")
                if error_messages:
                    messages.error(request, " ".join(error_messages))
                else:
                    messages.error(request, f"Validation error: {str(e)}")
                if request.user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('upload', instance_id=instance_id)
            except Exception as e:
                messages.error(request, f"Error saving images: {str(e)}")
                if request.user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('upload', instance_id=instance_id)

        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")
            if request.user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('upload', instance_id=instance_id)

    # For GET request, render the form
    
    if request.method == 'GET':
        
        if request.user.is_superuser:
            territory_id = request.GET.get('territory')
        else:
            territory_id = request.user.username
        obj=Territory.objects.get(territory=territory_id)
        img_obj = ThreeGenImage.objects.filter(territory__territory=territory_id)
        count = img_obj.count()
        try:
            existing = ThreeGenImage.objects.get(territory=obj, instance_id=instance_id)
            return render(request, 'core/upload.html', {
                'instance_id': instance_id,
                'data': existing,
                'obj': obj,
                'img_obj': img_obj,
                'count': count,
                'reupload':True,
                'territory_id': territory_id,
            })
        except ThreeGenImage.DoesNotExist:
            return render(request, 'core/upload.html', {
                'instance_id': instance_id,
                'obj': obj,
                'img_obj': img_obj,
                'count': count,
                'reupload':False,
                'territory_id': territory_id,
            })




@login_required
def territory_list(request):
    """
    Display a list of all territories with the number of doctors with uploaded data.
    """
    territories = Territory.objects.all()
    territory_data = []
    
    for territory in territories:
        doctor_count = ThreeGenImage.objects.filter(territory=territory).values('dr_rpl_id').distinct().count()
        territory_data.append({
            'id': territory.id,
            'territory': territory.territory,
            'territory_name': territory.territory_name,
            'doctor_count': doctor_count
        })
    
    return render(request, 'territory_list.html', {'territories': territory_data})

@login_required
def territory_detail(request, territory_code):
    """
    Display details of doctors and their images for a specific territory code.
    
    Args:
        request (HttpRequest): The HTTP request object.
        territory_code (str): The territory code.
        
    Returns:
        HttpResponse: The HTTP response object, render territory_detail template.
    """
    territory = get_object_or_404(Territory, territory=territory_code)
    images = ThreeGenImage.objects.filter(territory=territory)
    
    return render(request, 'territory_detail.html', {
        'territory': territory,
        'images': images
    })


@login_required
def territory_list_page(request):
    """
    Display a paginated list of all territories with the number of doctors with uploaded data.
    Handle search by territory code to redirect to the territory detail page.
    """
    # Handle search form submission
    if request.method == 'POST':
        territory_code = request.POST.get('territory_code', '').strip()
        if territory_code:
            try:
                Territory.objects.get(territory=territory_code)
                return redirect('territory_detail', territory_code=territory_code)
            except Territory.DoesNotExist:
                messages.error(request, f"Territory code '{territory_code}' not found.")
                return redirect('territory_list')

    # Get all territories
    territories = Territory.objects.all()
    
    # Set up pagination (10 territories per page)
    paginator = Paginator(territories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare territory data for the template
    territory_data = [
        {
            'id': territory.id,
            'territory': territory.territory,
            'territory_name': territory.territory_name,
            'region_name': territory.region_name,
            'zone_name': territory.zone_name,
            'doctor_count': ThreeGenImage.objects.filter(territory=territory).values('dr_rpl_id').distinct().count()
        }
        for territory in page_obj
    ]
    
    return render(request, 'territory_list.html', {
        'territories': territory_data,
        'page_obj': page_obj
    })
    
    
@login_required
def download(request):
    """
    Download the entire dr_images folder as a ZIP file, preserving the directory structure.
    """
    dr_images_path = os.path.join(settings.MEDIA_ROOT, 'dr_images')
    
    # Check if dr_images directory exists
    if not os.path.exists(dr_images_path):
        messages.error(request, "No images found in dr_images directory.")
        return redirect('territory_list')

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through the dr_images directory
        for root, _, files in os.walk(dr_images_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Compute the relative path for the ZIP file
                relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                zip_file.write(file_path, relative_path)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="dr_images.zip"'
    return response

@login_required
def export_excel(request):
    """
    Export the list of doctors and their images to an Excel file.
    """
    
    # Create a new workbook and add a worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Doctors Image Data"
    
    # Define the header row
    headers = ['Dr. RPL ID', 'Dr. Name', 'Territory ID', 'Territory Name', 'Region', 'Zone', 'Dr. Image', 'Parent Image', 'Children Image']
    worksheet.append(headers)
    
    # Populate the worksheet with data
    queryset = ThreeGenImage.objects.select_related('territory')
    for obj in queryset:
        dr_image = 'Yes' if obj.dr_image else 'No'
        parent_image = 'Yes' if obj.dr_parents_image else 'No'
        children_image = 'Yes' if obj.dr_children_image else 'No'
        row = [
            obj.dr_rpl_id,
            obj.dr_name,
            obj.territory.territory,
            obj.territory.territory_name,
            obj.territory.region_name,
            obj.territory.zone_name,
            dr_image,
            parent_image,
            children_image
        ]
        worksheet.append(row)
    
    # Save the workbook to a BytesIO object
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    
    # Create a response with the Excel file
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="doctors_threegen_imagedata.xlsx"'
    
    return response

@login_required
def doctor_view(request, instance_id):
    """
    View to handle uploading three generation images for a doctor.
    """
    territory = request.user.username
    obj=Territory.objects.get(territory=territory)
    img_obj= ThreeGenImage.objects.filter(territory__territory=territory)
    count = img_obj.count()
    try:
        doctor = ThreeGenImage.objects.get(territory__territory=territory, instance_id=instance_id)
    except ThreeGenImage.DoesNotExist:
        doctor = None
    return render(request, 'core/doctor.html', {'doctor': doctor, 'obj':obj, 'img_obj':img_obj, 'count':count , 'instance_id':instance_id})

@login_required
def delete_doctor(request, instance_id):
    territory = request.user.username
    if request.user.is_superuser:
        territory = request.GET.get('territory')
    obj = Territory.objects.get(territory=territory)
    img_obj = ThreeGenImage.objects.filter(territory__territory=territory)
    count = img_obj.count()
    zone = obj.zone_name
    region = obj.region_name
    try:
        doctor = ThreeGenImage.objects.get(territory__territory=territory,instance_id=instance_id)
        old_folder_name = f"{doctor.dr_rpl_id} - {doctor.dr_name}"
        old_folder_path = os.path.join(settings.MEDIA_ROOT, 'dr_images', zone, region, str(territory), old_folder_name)
        doctor.delete()
        if old_folder_path:
            try:
                shutil.rmtree(old_folder_path)
            except Exception as e:
                pass
        # {'obj':obj, 'img_obj':img_obj, 'count':count})
        messages.success(request, f"{doctor.dr_name} images deleted successfully.")
        img_obj = ThreeGenImage.objects.filter(territory__territory=territory)
        count = img_obj.count()
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('upload_preview')
    except ThreeGenImage.DoesNotExist:
        messages.error(request, "Invalid Doctor selected.")
        return redirect('upload_preview')
    
@login_required
def admin_dashboard(request):
    # Handle search form submission
    if request.method == 'POST':
        territory_code = request.POST.get('territory_code', '').strip()
        if territory_code:
            try:
                Territory.objects.get(territory=territory_code)
                return redirect('territory_detail', territory_code=territory_code)
            except Territory.DoesNotExist:
                messages.error(request, f"Territory code '{territory_code}' not found.")
                return redirect('territory_list')

    # Get all territories
    territories = Territory.objects.all()
    
    # Set up pagination (10 territories per page)
    paginator = Paginator(territories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare territory data for the template
    territory_data = [
        {
            'id': territory.id,
            'territory': territory.territory,
            'territory_name': territory.territory_name,
            'region_name': territory.region_name,
            'zone_name': territory.zone_name,
            'doctor_count': ThreeGenImage.objects.filter(territory=territory).values('dr_rpl_id').distinct().count()
        }
        for territory in page_obj
    ]
    return render(request, 'core/admin.html', {'territories': territory_data,'page_obj': page_obj})


@login_required 
def admin(request):
    if request.method == 'POST':
        territory_id = request.POST.get('territoryId')
        dr_rpl_id = request.POST.get('drRplId')
        dr_name = request.POST.get('drName')
        instance_id = request.POST.get('doctorId')
        dr_image = request.FILES.get('drImage')
        dr_parents_image = request.FILES.get('drParentImage')
        dr_children_image = request.FILES.get('drChildImage')
        
        if not territory_id:
            messages.error(request, "Territory ID is required.")
            return redirect('admin_dashboard')
        try:
            territory = Territory.objects.get(territory=territory_id)
        except Territory.DoesNotExist:
            messages.error(request, "Invalid Territory selected.")
            return redirect('admin_dashboard')
        
        try:
            img_obj = ThreeGenImage.objects.get(territory=territory, instance_id=instance_id)
            old_folder_name = f"{img_obj.dr_rpl_id} - {img_obj.dr_name}"
            zone = territory.zone_name
            region = territory.region_name
            old_folder_path = os.path.join(settings.MEDIA_ROOT, 'dr_images', zone, region, str(territory_id), old_folder_name)
            
            # Update data only if provided
            if dr_rpl_id:
                img_obj.dr_rpl_id = dr_rpl_id
            if dr_name:
                img_obj.dr_name = dr_name
            if dr_image:
                img_obj.dr_image = dr_image
            if dr_parents_image:
                img_obj.dr_parents_image = dr_parents_image
            if dr_children_image:
                img_obj.dr_children_image = dr_children_image
                
            new_folder_name = f"{img_obj.dr_rpl_id} - {img_obj.dr_name}"
        except ThreeGenImage.DoesNotExist:
            if not (dr_rpl_id and dr_name):
                messages.error(request, "Doctor RPL ID and Doctor Name are required.")
                return redirect('admin_dashboard')
            if not (dr_image and dr_parents_image and dr_children_image):
                messages.error(request, "All three images are required.")
                return redirect('admin_dashboard')
            img_obj = ThreeGenImage(
                territory=territory,
                instance_id=instance_id,
                dr_rpl_id=dr_rpl_id,
                dr_name=dr_name,
                dr_image=dr_image,
                dr_parents_image=dr_parents_image,
                dr_children_image=dr_children_image
            )
            old_folder_path = None
            old_folder_name = None
            new_folder_name = f"{dr_rpl_id} - {dr_name}"
        # Validate and Save
        try:
            img_obj.full_clean()
            img_obj.save()
            
            # Delete old folder if name changed
            if old_folder_path and old_folder_name != new_folder_name and os.path.exists(old_folder_path):
                shutil.rmtree(old_folder_path)
            messages.success(request, f"Images for {dr_name} (RPL ID: {dr_rpl_id}) uploaded successfully.")
            return redirect('admin_dashboard')
        except ValidationError as e:
            error_messages = []
            if isinstance(e.message_dict, dict):
                # Check for unique constraint on dr_rpl_id
                if 'dr_rpl_id' in e.message_dict:
                    error_messages.append(f"Doctor RPL ID '{dr_rpl_id}' already exists.")
                # Check for custom validation error for two-doctor limit
                if '__all__' in e.message_dict and any(
                    "maximum of two doctors" in msg.lower() for msg in e.message_dict['__all__']
                ):
                    error_messages.append("This territory already has two doctor images.")
            if error_messages:
                messages.error(request, " ".join(error_messages))
            else:
                messages.error(request, f"Validation error: {str(e)}")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Error saving images: {str(e)}")
            return redirect('admin_dashboard')
    
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        page_number = int(request.GET.get('page') or 1)
        per_page = int(request.GET.get("per_page") or 10)
        sort = request.GET.get("sort", "territory") 
        direction = request.GET.get("direction", "asc")        
        
        data = ThreeGenImage.objects.select_related('territory').all()
        
        if search_query:
            data = data.filter(
                Q(dr_rpl_id__icontains=search_query) |
                Q(dr_name__icontains=search_query) |
                Q(territory__territory__icontains=search_query) |
                Q(territory__territory_name__icontains=search_query) |
                Q(territory__region_name__icontains=search_query) |
                Q(territory__zone_name__icontains=search_query)
            )
            
        sort_by = sort
        if sort_by == "territory":
            sort_by = "territory__territory"
        elif sort_by == "territory_name":
            sort_by = "territory__territory_name"
        elif sort_by == "region":
            sort_by = "territory__region_name"
        elif sort_by == "zone":
            sort_by = "territory__zone_name"
        elif sort_by == "dr_id":
            sort_by = "dr_rpl_id"
        
        if direction == "desc":
            sort_by = f"-{sort_by}"
        data = data.order_by(sort_by)
            
        paginator = Paginator(data, per_page)
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'dashboard/dashboard.html', {'data': page_obj, 'search_query': search_query, 'per_page': per_page, 'sort': sort, 'direction': direction})
        # return render(request, 'core/admin.html', {'data': page_obj, 'search_query': search_query, 'per_page': per_page, 'sort': sort, 'direction': direction})