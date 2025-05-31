from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.encoding import smart_str
import os
import mimetypes
import logging

from .models import Material, MaterialCategory, Download
from courses.models import Subject

logger = logging.getLogger(__name__)

def materials_list(request):
    """Lista de materiais com filtros e paginação"""
    materials = Material.objects.all().order_by('-created_at')
    categories = MaterialCategory.objects.all()
    subjects = Subject.objects.filter(is_active=True)
    
    # Filtros
    category_id = request.GET.get('category')
    subject_id = request.GET.get('subject')
    material_type = request.GET.get('type')
    search = request.GET.get('search')
    
    if category_id:
        try:
            materials = materials.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass
    
    if subject_id:
        try:
            materials = materials.filter(subject_id=int(subject_id))
        except (ValueError, TypeError):
            pass
    
    if material_type:
        materials = materials.filter(material_type=material_type)
    
    if search:
        materials = materials.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Paginação
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
    """Download de material com verificação de acesso"""
    try:
        material = get_object_or_404(Material, id=material_id)
        
        # Verificar se usuário tem acesso
        if material.is_premium and not request.user.is_premium:
            messages.error(request, 'Este material é exclusivo para assinantes premium.')
            return redirect('materials:materials_list')
        
        # Registrar download
        download, created = Download.objects.get_or_create(
            user=request.user,
            material=material
        )
        
        if created:
            material.download_count += 1
            material.save()
        
        # Processar download
        if material.file:
            try:
                # Verificar se arquivo existe
                if not os.path.exists(material.file.path):
                    messages.error(request, 'Arquivo não encontrado no servidor.')
                    return redirect('materials:materials_list')
                
                # Preparar download
                response = FileResponse(
                    open(material.file.path, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(material.file.name)
                )
                return response
                
            except Exception as e:
                logger.error(f"Erro ao servir arquivo {material_id}: {e}")
                messages.error(request, 'Erro ao baixar arquivo. Tente novamente.')
                return redirect('materials:materials_list')
        
        elif material.external_url:
            return redirect(material.external_url)
        
        else:
            messages.error(request, 'Material não possui arquivo para download.')
            return redirect('materials:materials_list')
    
    except Material.DoesNotExist:
        messages.error(request, 'Material não encontrado.')
        return redirect('materials:materials_list')
    except Exception as e:
        logger.error(f"Erro inesperado no download {material_id}: {e}")
        messages.error(request, 'Erro interno. Tente novamente.')
        return redirect('materials:materials_list')