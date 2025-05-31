/**
 * Gerenciador de Downloads - EEAR System
 * Gerencia o estado visual dos botões de download
 */

class DownloadManager {
    constructor() {
        this.downloadInProgress = new Set();
        this.init();
    }
    
    init() {
        this.setupDownloadButtons();
        this.setupVisibilityDetection();
    }
    
    setupDownloadButtons() {
        const downloadButtons = document.querySelectorAll('a[href*="/download/"]');
        
        downloadButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleDownloadClick(button, e);
            });
        });
    }
    
    handleDownloadClick(button, event) {
        const originalContent = button.innerHTML;
        const materialId = this.extractMaterialId(button.href);
        const isExternalLink = this.isExternalLink(button);
        
        // Salvar estado original
        button.setAttribute('data-original-content', originalContent);
        button.setAttribute('data-material-id', materialId);
        
        if (isExternalLink) {
            this.handleExternalLink(button);
        } else {
            this.handleFileDownload(button, event);
        }
    }
    
    isExternalLink(button) {
        return button.innerHTML.includes('Abrir') || 
               button.title.includes('link') ||
               button.querySelector('i.fa-external-link-alt');
    }
    
    extractMaterialId(href) {
        const match = href.match(/\/download\/(\d+)\//);
        return match ? match[1] : null;
    }
    
    handleExternalLink(button) {
        const originalContent = button.getAttribute('data-original-content');
        
        // Estado de carregamento para links externos
        button.innerHTML = '<i class="fas fa-external-link-alt me-1"></i>Abrindo...';
        button.style.pointerEvents = 'none';
        
        // Restaurar rapidamente para links externos
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-check me-1"></i>Aberto!';
            button.style.backgroundColor = '#17a2b8';
            
            setTimeout(() => {
                this.restoreButton(button);
            }, 1500);
        }, 800);
    }
    
    handleFileDownload(button, event) {
        const materialId = button.getAttribute('data-material-id');
        
        // Adicionar à lista de downloads em progresso
        this.downloadInProgress.add(materialId);
        
        // Estado de carregamento
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Baixando...';
        button.style.pointerEvents = 'none';
        button.style.opacity = '0.8';
        
        // Usar iframe invisível para download
        this.triggerDownloadWithIframe(button.href, () => {
            this.onDownloadComplete(button, materialId);
        });
        
        // Fallback de segurança
        setTimeout(() => {
            if (this.downloadInProgress.has(materialId)) {
                this.onDownloadComplete(button, materialId);
            }
        }, 8000);
        
        // Cancelar navegação padrão
        event.preventDefault();
    }
    
    triggerDownloadWithIframe(url, callback) {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.style.width = '0';
        iframe.style.height = '0';
        
        let callbackExecuted = false;
        
        const executeCallback = () => {
            if (!callbackExecuted) {
                callbackExecuted = true;
                callback();
                // Remover iframe após um tempo
                setTimeout(() => {
                    if (iframe.parentNode) {
                        document.body.removeChild(iframe);
                    }
                }, 2000);
            }
        };
        
        // Tentar detectar quando o download começou
        iframe.onload = () => {
            setTimeout(executeCallback, 1000);
        };
        
        iframe.onerror = () => {
            executeCallback();
        };
        
        document.body.appendChild(iframe);
        iframe.src = url;
        
        // Backup: executar callback após 3 segundos
        setTimeout(executeCallback, 3000);
    }
    
    onDownloadComplete(button, materialId) {
        this.downloadInProgress.delete(materialId);
        
        // Estado de sucesso
        button.innerHTML = '<i class="fas fa-check-circle me-1"></i>Baixado!';
        button.style.backgroundColor = '#28a745';
        button.style.color = 'white';
        button.style.opacity = '1';
        
        // Restaurar após 2 segundos
        setTimeout(() => {
            this.restoreButton(button);
        }, 2000);
    }
    
    restoreButton(button) {
        const originalContent = button.getAttribute('data-original-content');
        
        if (originalContent) {
            button.innerHTML = originalContent;
            button.style.pointerEvents = 'auto';
            button.style.backgroundColor = '';
            button.style.color = '';
            button.style.opacity = '';
            
            // Limpar atributos
            button.removeAttribute('data-original-content');
            button.removeAttribute('data-material-id');
        }
    }
    
    setupVisibilityDetection() {
        // Detectar quando o usuário volta à aba
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.downloadInProgress.size > 0) {
                // Restaurar todos os downloads em progresso após um breve delay
                setTimeout(() => {
                    this.downloadInProgress.forEach(materialId => {
                        const button = document.querySelector(`[data-material-id="${materialId}"]`);
                        if (button) {
                            this.onDownloadComplete(button, materialId);
                        }
                    });
                }, 1000);
            }
        });
        
        // Detectar quando o usuário sai da página
        window.addEventListener('beforeunload', () => {
            // Limpar todos os downloads em progresso
            this.downloadInProgress.clear();
        });
    }
    
    // Método público para restaurar todos os botões
    restoreAllButtons() {
        const buttonsWithState = document.querySelectorAll('[data-original-content]');
        buttonsWithState.forEach(button => {
            this.restoreButton(button);
        });
        this.downloadInProgress.clear();
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.downloadManager = new DownloadManager();
    
    // Expor função global para restaurar botões
    window.restoreDownloadButtons = () => {
        if (window.downloadManager) {
            window.downloadManager.restoreAllButtons();
        }
    };
});

// Auto-restaurar se houver botões em estado de loading após carregamento da página
window.addEventListener('load', function() {
    setTimeout(() => {
        if (window.downloadManager) {
            window.downloadManager.restoreAllButtons();
        }
    }, 1000);
});