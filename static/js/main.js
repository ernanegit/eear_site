// Função para obter CSRF token
function getCSRFToken() {
    // Tenta obter de várias fontes possíveis
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;
    
    const csrfMeta = document.querySelector('meta[name=csrf-token]');
    if (csrfMeta) return csrfMeta.getAttribute('content');
    
    // Tenta obter do cookie (se configurado)
    const csrfCookie = getCookie('csrftoken');
    if (csrfCookie) return csrfCookie;
    
    return null;
}

// Função para obter cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Mark lesson as complete - Corrigido com melhor tratamento de erro
function markLessonComplete(lessonId) {
    const csrfToken = getCSRFToken();
    
    if (!csrfToken) {
        showAlert('Erro de segurança. Recarregue a página e tente novamente.', 'error');
        return;
    }
    
    // Desabilitar botão para evitar cliques duplos
    const button = document.getElementById('complete-btn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
    }
    
    fetch(`/courses/lesson/${lessonId}/complete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'lesson_id': lessonId,
            'completed': true
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update UI
            if (button) {
                button.innerHTML = '<i class="fas fa-check me-2"></i>Concluída';
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                button.disabled = true;
            }
            
            // Atualizar barra de progresso se existir
            updateProgressBar();
            
            // Show success message
            showAlert('Aula marcada como concluída!', 'success');
            
            // Opcional: redirecionar para próxima aula após alguns segundos
            const nextLessonBtn = document.querySelector('[data-next-lesson]');
            if (nextLessonBtn) {
                setTimeout(() => {
                    if (confirm('Deseja ir para a próxima aula?')) {
                        window.location.href = nextLessonBtn.href;
                    }
                }, 2000);
            }
        } else {
            throw new Error(data.message || 'Erro desconhecido');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Restaurar botão
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-check me-2"></i>Marcar como Concluída';
        }
        
        showAlert('Erro ao marcar aula como concluída. Tente novamente.', 'error');
    });
}

// Atualizar barra de progresso
function updateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        // Incrementar progresso (isso seria melhor calculado no backend)
        const currentWidth = parseInt(progressBar.style.width) || 0;
        const newWidth = Math.min(currentWidth + 10, 100); // Incremento simplificado
        progressBar.style.width = newWidth + '%';
        progressBar.setAttribute('aria-valuenow', newWidth);
    }
}

// Show alert messages - Melhorado
function showAlert(message, type = 'info', duration = 5000) {
    // Remover alerts anteriores do mesmo tipo
    const existingAlerts = document.querySelectorAll(`.alert-${type === 'error' ? 'danger' : type}`);
    existingAlerts.forEach(alert => alert.remove());
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Inserir no topo da página
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
    
    // Scroll para o topo para mostrar o alert
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Obter ícone para o alert
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Progress tracking for videos - Melhorado
function trackVideoProgress(videoElement, lessonId) {
    if (!videoElement || !lessonId) return;
    
    let progressSent = false;
    let lastUpdateTime = 0;
    const updateInterval = 30; // Atualizar a cada 30 segundos
    
    videoElement.addEventListener('timeupdate', function() {
        const currentTime = this.currentTime;
        const duration = this.duration;
        
        if (!duration) return;
        
        const progress = (currentTime / duration) * 100;
        
        // Atualizar progresso no servidor periodicamente
        if (currentTime - lastUpdateTime >= updateInterval) {
            updateWatchTime(lessonId, currentTime);
            lastUpdateTime = currentTime;
        }
        
        // Mark as complete when 90% watched
        if (progress >= 90 && !progressSent) {
            markLessonComplete(lessonId);
            progressSent = true;
        }
    });
    
    // Salvar progresso quando o vídeo for pausado
    videoElement.addEventListener('pause', function() {
        updateWatchTime(lessonId, this.currentTime);
    });
    
    // Salvar progresso quando sair da página
    window.addEventListener('beforeunload', function() {
        if (videoElement.currentTime > 0) {
            updateWatchTime(lessonId, videoElement.currentTime);
        }
    });
}

// Atualizar tempo assistido
function updateWatchTime(lessonId, watchTime) {
    const csrfToken = getCSRFToken();
    if (!csrfToken) return;
    
    fetch(`/courses/lesson/${lessonId}/update-progress/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'watch_time': Math.round(watchTime)
        })
    }).catch(error => {
        console.error('Error updating watch time:', error);
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { "show": 500, "hide": 100 }
        });
    });
}

// Search functionality - Melhorado
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        
        // Debounce para evitar muitas pesquisas
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });
}

// Realizar pesquisa
function performSearch(query) {
    const items = document.querySelectorAll('.searchable-item');
    let visibleCount = 0;
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const isVisible = !query || text.includes(query);
        
        item.style.display = isVisible ? '' : 'none';
        if (isVisible) visibleCount++;
    });
    
    // Mostrar mensagem se nenhum resultado
    const noResultsMessage = document.getElementById('no-results-message');
    if (noResultsMessage) {
        noResultsMessage.style.display = visibleCount === 0 && query ? 'block' : 'none';
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form validation helpers
function validateForm(formElement) {
    if (!formElement) return true;
    
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'Este campo é obrigatório');
            isValid = false;
        } else {
            clearFieldError(input);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorMsg = field.parentNode.querySelector('.invalid-feedback');
    if (errorMsg) {
        errorMsg.remove();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initSearch();
    initSmoothScrolling();
    
    // Auto-hide alerts after specified time
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
    
    // Form validation on submit
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showAlert('Por favor, corrija os erros no formulário', 'error');
            }
        });
    });
    
    // Video progress tracking
    const videoElement = document.querySelector('video, iframe[src*="youtube"], iframe[src*="vimeo"]');
    const lessonId = document.querySelector('[data-lesson-id]')?.dataset.lessonId;
    
    if (videoElement && lessonId) {
        trackVideoProgress(videoElement, lessonId);
    }
    
    console.log('EEAR System initialized successfully');
});