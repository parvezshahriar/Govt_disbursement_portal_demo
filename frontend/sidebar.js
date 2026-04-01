// Load Sidebar HTML
function loadSidebar() {
    const sidebarContainer = document.getElementById('sidebar-container');
    if (!sidebarContainer) {
        console.error('Sidebar container not found');
        return;
    }

    // Get user role from localStorage
    const userRole = localStorage.getItem('userRole');
    console.log('[SIDEBAR] User role:', userRole);

    // Dashboard button visibility - only for admin users (case-insensitive)
    const isAdmin = userRole && userRole.toLowerCase() === 'admin';
    const dashboardItem = isAdmin ?
        `<li class="sidebar-item" data-page="dashboard" data-admin="true" onclick="handleSidebarClick(this, 'dashboard')"><i class="fa-solid fa-file-upload"></i> Dashboard</li>` :
        `<li class="sidebar-item" data-page="dashboard" data-admin="false" style="display: none;"><i class="fa-solid fa-file-upload"></i> Dashboard</li>`;

    // Inline sidebar HTML to avoid fetch issues
    const sidebarHTML = `<aside class="sidebar">
    <div class="brand">
        <div class="logo-wrapper">
            <img src="logo.png" alt="Nagad Logo" class="sidebar-logo">
        </div>
    </div>
    
    <div class="sidebar-menu">
        <h3>Government Disbursement</h3>
        <ul>
            ${dashboardItem}
            <li class="sidebar-item" data-page="upload" onclick="handleSidebarClick(this, 'upload')"><i class="fa-solid fa-file-upload"></i> Upload</li>
            <li class="sidebar-item" data-page="upload-history" onclick="handleSidebarClick(this, 'upload-history')"><i class="fa-solid fa-file-upload"></i> Upload History</li>
            <li class="sidebar-item" data-page="transaction-history" onclick="handleSidebarClick(this, 'transaction-history')"><i class="fa-solid fa-list"></i> Transaction History</li>
            <li class="sidebar-item" data-page="audit-history" onclick="handleSidebarClick(this, 'audit-history')"><i class="fa-solid fa-shield-halved"></i> Audit History</li>
        </ul>
    </div>
    
    <div class="sidebar-footer">
        <i class="fa-solid fa-angles-right"></i>
    </div>
</aside>`;

    sidebarContainer.innerHTML = sidebarHTML;
    console.log('[SIDEBAR] Sidebar loaded successfully');

    // Set active sidebar item based on current page
    setActiveSidebarItem();
}

// Function to set active sidebar item based on current page
function setActiveSidebarItem() {
    const currentPage = window.location.pathname.split('/').pop();
    const activePage = localStorage.getItem('activePage') || null;

    console.log('[SIDEBAR] Current page:', currentPage);
    console.log('[SIDEBAR] Active page from storage:', activePage);

    // Use activePage from localStorage if available, otherwise map from URL
    let pageToHighlight = activePage;
    if (!pageToHighlight) {
        // Map file names to sidebar data-page values
        const pageMap = {
            'index.html': 'dashboard',
            'image-upload.html': 'upload',
            'admin-dashboard.html': 'dashboard',
            'upload_history.html': 'upload-history',
            'audit_dashboard.html': 'audit-history'
        };
        pageToHighlight = pageMap[currentPage] || null;
    }

    console.log('[SIDEBAR] Page to highlight:', pageToHighlight);

    if (pageToHighlight) {
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-page') === pageToHighlight) {
                item.classList.add('active');
                console.log('[SIDEBAR] Highlighted item:', item.textContent);
            }
        });
        // Clear the flag after using it
        localStorage.removeItem('activePage');
    }
}

// Sidebar menu click handler - Make it global so onclick works
window.handleSidebarClick = function (element, page) {
    console.log('[SIDEBAR] handleSidebarClick called for page:', page);

    // Remove active class from all sidebar items
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to clicked item
    element.classList.add('active');
    console.log('[SIDEBAR] Applied active class to:', element.textContent.trim());

    // Handle page navigation/content change
    console.log('[SIDEBAR] Navigating to:', page);

    switch (page) {
        case 'dashboard':
            console.log('[SIDEBAR] Dashboard clicked');
            const userRole = localStorage.getItem('userRole');
            console.log('[SIDEBAR] User role:', userRole);
            if (userRole && userRole.toLowerCase() === 'admin') {
                console.log('[SIDEBAR] Admin user - navigating to admin-dashboard.html');
                window.location.href = 'admin-dashboard.html';
            } else {
                console.log('[SIDEBAR] Regular user - navigating to index.html');
                window.location.href = 'index.html';
            }
            break;
        case 'upload':
            console.log('[SIDEBAR] Upload clicked');
            loadUploadPage();
            break;
        case 'upload-history':
            console.log('[SIDEBAR] Loading Upload History');
            loadUploadHistory();
            break;
        case 'transaction-history':
            console.log('[SIDEBAR] Loading Transaction History');
            loadTransactionHistory();
            break;
        case 'audit-history':
            console.log('[SIDEBAR] Loading Audit History');
            loadAuditHistory();
            break;
    }
};

// Function to load Upload page
window.loadUploadPage = function () {
    console.log('[SIDEBAR] Upload page function called');
    // Set the active page flag before navigation
    localStorage.setItem('activePage', 'upload');
    // Navigate to the upload page
    window.location.href = 'index.html';
};

// Function to load Upload History for non-admin users
window.loadUploadHistory = function () {
    console.log('[SIDEBAR] Upload History function called');
    // Set the active page flag before navigation
    localStorage.setItem('activePage', 'upload-history');
    // Navigate to the upload history page
    window.location.href = 'upload_history.html';
};

// Function to load Transaction History for non-admin users
window.loadTransactionHistory = function () {
    console.log('[SIDEBAR] Transaction History function called');
    // Placeholder for transaction history content
    // This will load the transaction history page or content
    alert('Transaction History page - Feature coming soon');
};

// Function to load Audit History for non-admin users
window.loadAuditHistory = function () {
    console.log('[SIDEBAR] Audit History function called');
    // Set the active page flag before navigation
    localStorage.setItem('activePage', 'audit-history');
    // Navigate to the unified audit dashboard
    window.location.href = 'audit_dashboard.html';
};

// Load sidebar when DOM is ready or immediately if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadSidebar);
} else {
    loadSidebar();
}
