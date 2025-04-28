from django.shortcuts import render
from .models import Territory,ThreeGenImage

def get_img_obj(territory):
    try:
        obj = ThreeGenImage.objects.filter(territory=territory)
        count = len(obj)
    except:
        obj = None
        count = 0
    print('this is from utils', count)
    return [obj, count]

def render_upload_preview(request,territory):
    obj=Territory.objects.get(territory=territory)
    img_obj= ThreeGenImage.objects.filter(territory__territory=territory)
    count = img_obj.count()
    return render(request, 'upload_preview.html', {'obj':obj, 'img_obj':img_obj, 'count':count})