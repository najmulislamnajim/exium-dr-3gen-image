import os
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class Territory(models.Model):
    """
    Model to store Terriotory.

    Attributes:
        territory (CharFiled): Territory code (unique).
        territory_name (CharField): Name of the terrytory (mandatory).
        region_name (CharField): Name of the region (mandatory).
        zone_name (CharField): Name of the zone (mandatory).
    """
    territory = models.CharField(max_length=10, unique=True)
    territory_name = models.CharField(max_length=100)
    region_name = models.CharField(max_length=100)
    zone_name = models.CharField(max_length=100)

    def __str__(self):
        return self.territory_name

    class Meta:
        db_table = 'rpl_territory' 
        verbose_name = 'Territory'
        verbose_name_plural = 'Territories'

def get_image_upload_path(instance, filename):
    """
    Generate a structured upload path and filename for images.
    
    Args:
        instance (ThreeGenImage): The ThreeGenImage instance.
        filename (str): The name of the uploaded file.
        
    Returns:
        str: The constructed upload path.
    """
    # Determine image type
    if 'dr_image' in instance.__dict__ and filename == instance.dr_image.name:
        image_type = ''
    elif 'dr_parents_image' in instance.__dict__ and filename == instance.dr_parents_image.name:
        image_type = 'parent'
    else:
        image_type = 'children'
    # Extract file extension
    ext = os.path.splitext(filename)[1]
    
    territory_obj = Territory.objects.get(territory=instance.territory.territory)
    zone = territory_obj.zone_name
    region = territory_obj.region_name
    # Construct filename
    filename = f"{zone}_{region}_{instance.territory.territory}_{instance.dr_rpl_id}_{instance.dr_name}_{image_type}{ext}"
    
    # Construct folder name 
    dr_folder = instance.dr_rpl_id + ' - ' + instance.dr_name
    
    # Construct path and return
    return os.path.join('dr_images',zone, region, instance.territory.territory, dr_folder, filename)
        
class ThreeGenImage(models.Model):
    """
    Model to store doctors three generation images.

    Attributes:
        territory (ForeignKey): The territory code.
        dr_rpl_id (CharField): Doctors RPL ID (unique).
        dr_image (ImageField): Uploaded doctor image.
        dr_parents_image (ImageField): Uploaded doctor parent image.
        dr_children_image (ImageField): Uploaded doctor children image.
        uploaded_at (DateTimeField): Timestamp of the upload.
    """
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE)
    dr_rpl_id = models.CharField(max_length=10, unique=True)
    dr_name = models.CharField(max_length=100)
    dr_image = models.ImageField(upload_to=get_image_upload_path, null=True, blank=True, max_length=255)
    dr_parents_image = models.ImageField(upload_to=get_image_upload_path, null=True, blank=True, max_length=255)
    dr_children_image = models.ImageField(upload_to=get_image_upload_path, null=True, blank=True, max_length=255)
    instance_id = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Validate that the territory does not exceed two doctors.
        """ 
        if not self.pk:  # Only check for new instances
            doctor_count = ThreeGenImage.objects.filter(territory=self.territory).values('dr_rpl_id').distinct().count()
            if doctor_count >= 2 and not ThreeGenImage.objects.filter(territory=self.territory, dr_rpl_id=self.dr_rpl_id).exists():
                raise ValidationError(f"Territory '{self.territory}' already has images for two doctors. Cannot add another.")

    def save(self, *args, **kwargs):
        """
        Override save to run validation before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return a string representation of the ThreeGenImage instance.
        """
        return f"{self.dr_rpl_id} - {self.dr_name}"

    class Meta:
        """
        Meta class for ThreeGenImage model.
        """
        db_table = 'three_gen_image'
        verbose_name = 'Three Gen Image'
        verbose_name_plural = 'Three Gen Images'