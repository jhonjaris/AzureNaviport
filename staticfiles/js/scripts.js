// NaviPort RD - Scripts principales

document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad del dropdown de usuario
    const userAvatar = document.querySelector('.user-avatar');
    const userDropdown = document.querySelector('.user-dropdown');
    const navbarUser = document.querySelector('.navbar-user');
    
    if (userAvatar && userDropdown) {
        // Toggle dropdown al hacer clic en el avatar
        userAvatar.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (userDropdown.style.opacity === '1') {
                userDropdown.style.opacity = '0';
                userDropdown.style.visibility = 'hidden';
                userDropdown.style.transform = 'translateY(-10px)';
            } else {
                userDropdown.style.opacity = '1';
                userDropdown.style.visibility = 'visible';
                userDropdown.style.transform = 'translateY(0)';
            }
        });
        
        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!navbarUser.contains(e.target)) {
                userDropdown.style.opacity = '0';
                userDropdown.style.visibility = 'hidden';
                userDropdown.style.transform = 'translateY(-10px)';
            }
        });
        
        // Mantener dropdown abierto al hacer hover
        navbarUser.addEventListener('mouseenter', function() {
            userDropdown.style.opacity = '1';
            userDropdown.style.visibility = 'visible';
            userDropdown.style.transform = 'translateY(0)';
        });
        
        navbarUser.addEventListener('mouseleave', function() {
            setTimeout(function() {
                if (!navbarUser.matches(':hover')) {
                    userDropdown.style.opacity = '0';
                    userDropdown.style.visibility = 'hidden';
                    userDropdown.style.transform = 'translateY(-10px)';
                }
            }, 100);
        });
    }
    
    // Confirmación para logout
    const logoutLinks = document.querySelectorAll('.logout-link');
    logoutLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro que desea cerrar la sesión?')) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    console.log('NaviPort RD scripts cargados correctamente');
});