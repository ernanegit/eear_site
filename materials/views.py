from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Material, MaterialCategory, Download
from courses.models import Subject

def materials_list(request):
    materials = Material.objects.all().order_by('-created_at')
    categories = MaterialCategory.objects.all()
    subjects = Subject.objects.filter(is_active=True)
    
    # Filters
    category_id = request.GET.get('category')
    subject_id = request.GET.get('subject')
    material_type = request.GET.get('type')
    search = request.GET.get('search')
    
    if category_id:
        materials = materials.filter(category_id=category_id)
    
    if subject_id:
        materials = materials.filter(subject_id=subject_id)
    
    if material_type:
        materials = materials.filter(material_type=material_type)
    
    if search:
        materials = materials.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(materials, 12)
    page_number = request.GET.get('page')
    materials = paginator.get_page(page_number)
    
    context = {
        'materials': materials,
        'categories': categories,
        'subjects': subjects,
        'search': search,
    }
    return render(request, 'materials/materials_list.html', context)

@login_required
def download_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    
    # Check if user has access
    if material.is_premium and not request.user.is_premium:
        messages.error(request, 'Este material é exclusivo para assinantes premium.')
        return redirect('materials:materials_list')
    
    # Record download
    download, created = Download.objects.get_or_create(
        user=request.user,
        material=material
    )
    
    if created:
        material.download_count += 1
        material.save()
    
    if material.file:
        # Serve file
        response = HttpResponse(material.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{material.file.name}"'
        return response
    elif material.external_url:
        return redirect(material.external_url)
    else:
        raise Http404("Material não encontrado")

# Create your views here.
