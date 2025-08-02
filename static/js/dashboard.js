// Dashboard JavaScript functionality
let currentPage = 1;
let currentFilters = {
    category: 'all',
    source: 'all',
    start_date: '',
    end_date: '',
    search: '',
    per_page: 20
};
let allSources = [];

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadSources();
    loadMessages();
    updateLastUpdated();
    
    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Filter change listeners
    document.getElementById('categoryFilter').addEventListener('change', function() {
        currentFilters.category = this.value;
        currentPage = 1;
        loadMessages();
    });
    
    document.getElementById('startDate').addEventListener('change', function() {
        currentFilters.start_date = this.value;
        currentPage = 1;
        loadMessages();
    });
    
    document.getElementById('endDate').addEventListener('change', function() {
        currentFilters.end_date = this.value;
        currentPage = 1;
        loadMessages();
    });
    
    document.getElementById('searchInput').addEventListener('input', debounce(function() {
        currentFilters.search = this.value;
        currentPage = 1;
        loadMessages();
    }, 500));
    
    document.getElementById('perPageSelect').addEventListener('change', function() {
        currentFilters.per_page = parseInt(this.value);
        currentPage = 1;
        loadMessages();
    });
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load available sources for filtering
async function loadSources() {
    try {
        const response = await fetch('/api/sources');
        const sources = await response.json();
        allSources = sources;
        
        const dropdown = document.getElementById('sourceDropdownMenu');
        const existingOptions = dropdown.querySelectorAll('li:not(:first-child):not(:nth-child(2))');
        existingOptions.forEach(li => li.remove());
        
        sources.forEach(source => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="dropdown-item">
                    <input class="form-check-input me-2" type="checkbox" 
                           value="${source.name}" id="source-${source.name.replace(/\s+/g, '-')}"
                           onchange="updateSourceSelection()">
                    <label class="form-check-label" for="source-${source.name.replace(/\s+/g, '-')}">
                        ${source.name} (${source.count})
                    </label>
                </div>
            `;
            dropdown.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading sources:', error);
    }
}

// Update source selection
function updateSourceSelection() {
    const checkboxes = document.querySelectorAll('#sourceDropdownMenu input[type="checkbox"]');
    const allCheckbox = document.getElementById('source-all');
    const selectedSources = [];
    
    checkboxes.forEach(checkbox => {
        if (checkbox.checked && checkbox.value !== 'all') {
            selectedSources.push(checkbox.value);
        }
    });
    
    if (selectedSources.length === 0) {
        allCheckbox.checked = true;
        currentFilters.source = 'all';
        document.getElementById('sourceDropdownText').textContent = 'All Sources';
    } else {
        allCheckbox.checked = false;
        currentFilters.source = selectedSources.join(',');
        const displayText = selectedSources.length === 1 ? 
            selectedSources[0] : 
            `${selectedSources.length} sources selected`;
        document.getElementById('sourceDropdownText').textContent = displayText;
    }
    
    document.getElementById('selectedSources').value = currentFilters.source;
    currentPage = 1;
    loadMessages();
}

// Handle "All Sources" checkbox
document.addEventListener('change', function(e) {
    if (e.target.id === 'source-all') {
        const checkboxes = document.querySelectorAll('#sourceDropdownMenu input[type="checkbox"]:not(#source-all)');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        currentFilters.source = 'all';
        document.getElementById('sourceDropdownText').textContent = 'All Sources';
        document.getElementById('selectedSources').value = 'all';
        currentPage = 1;
        loadMessages();
    }
});

// Load messages with current filters
async function loadMessages() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            ...currentFilters,
            page: currentPage
        });
        
        const response = await fetch(`/api/data?${params}`);
        const result = await response.json();
        
        displayMessages(result.data);
        updatePagination(result);
        updateMessageCount(result.total);
        
    } catch (error) {
        console.error('Error loading messages:', error);
        showError('Failed to load messages. Please try again.');
    }
}

// Display messages in the container
function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No messages found</h5>
                <p class="text-muted">Try adjusting your filters or search terms.</p>
            </div>
        `;
        return;
    }
    
    const messagesHtml = messages.map(message => createMessageCard(message)).join('');
    container.innerHTML = messagesHtml;
}

// Create HTML for a single message card
function createMessageCard(message) {
    const categoryBadge = message.Category === 'Relevant' ? 
        '<span class="badge badge-relevant">Relevant Job</span>' :
        '<span class="badge badge-uncategorized">Uncategorized</span>';
    
    const messagePreview = truncateText(message['Full Message'] || '', 200);
    const links = message.extracted_links || [];
    
    const linksHtml = links.length > 0 ? 
        `<div class="mt-2">
            ${links.slice(0, 3).map(link => 
                `<a href="${link}" target="_blank" class="link-pill">${getDomainFromUrl(link)}</a>`
            ).join('')}
            ${links.length > 3 ? `<span class="text-muted">+${links.length - 3} more</span>` : ''}
        </div>` : '';
    
    return `
        <div class="card message-card mb-3" onclick="viewMessage('${message['Message ID']}')">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="card-title mb-0">
                        <i class="fas fa-users text-primary"></i>
                        ${message['Source Group'] || 'Unknown Source'}
                    </h6>
                    <div>
                        ${categoryBadge}
                        <small class="text-muted ms-2">
                            <i class="fas fa-calendar"></i>
                            ${message['Message Date']} ${message['Message Time']}
                        </small>
                    </div>
                </div>
                <div class="message-preview">
                    <p class="card-text">${messagePreview}</p>
                </div>
                ${linksHtml}
            </div>
        </div>
    `;
}

// View individual message
function viewMessage(messageId) {
    window.open(`/message/${messageId}`, '_blank');
}

// Utility functions
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function getDomainFromUrl(url) {
    try {
        const domain = new URL(url.startsWith('http') ? url : 'http://' + url).hostname;
        return domain.replace('www.', '');
    } catch {
        return url.substring(0, 30);
    }
}

function showLoading() {
    document.getElementById('messagesContainer').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin fa-2x"></i>
            <p>Loading messages...</p>
        </div>
    `;
}

function showError(message) {
    document.getElementById('messagesContainer').innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        </div>
    `;
}

// Update pagination
function updatePagination(result) {
    const pagination = document.getElementById('pagination');
    const totalPages = result.total_pages;
    const currentPageNum = result.page;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHtml = '';
    
    // Previous button
    if (currentPageNum > 1) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${currentPageNum - 1})">Previous</a>
            </li>
        `;
    }
    
    // Page numbers
    const startPage = Math.max(1, currentPageNum - 2);
    const endPage = Math.min(totalPages, currentPageNum + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPageNum ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    if (currentPageNum < totalPages) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${currentPageNum + 1})">Next</a>
            </li>
        `;
    }
    
    pagination.innerHTML = paginationHtml;
}

function changePage(page) {
    currentPage = page;
    loadMessages();
    window.scrollTo(0, 0);
}

function updateMessageCount(count) {
    document.getElementById('messageCount').textContent = count;
}

function updateLastUpdated() {
    const now = new Date().toLocaleString();
    document.getElementById('lastUpdated').innerHTML = `
        <i class="fas fa-clock"></i> Last updated: ${now}
    `;
}

// Filter control functions
function clearFilters() {
    // Reset all filter values
    document.getElementById('categoryFilter').value = 'all';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('searchInput').value = '';
    document.getElementById('perPageSelect').value = '20';
    
    // Reset source selection
    document.getElementById('source-all').checked = true;
    const sourceCheckboxes = document.querySelectorAll('#sourceDropdownMenu input[type="checkbox"]:not(#source-all)');
    sourceCheckboxes.forEach(checkbox => checkbox.checked = false);
    document.getElementById('sourceDropdownText').textContent = 'All Sources';
    
    // Reset current filters
    currentFilters = {
        category: 'all',
        source: 'all',
        start_date: '',
        end_date: '',
        search: '',
        per_page: 20
    };
    
    currentPage = 1;
    loadMessages();
}

function refreshData() {
    loadSources();
    loadMessages();
    updateLastUpdated();
}

// Export function for individual messages
function exportMessage(messageData) {
    const dataStr = JSON.stringify(messageData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `message_${messageData['Message ID']}.json`;
    link.click();
    URL.revokeObjectURL(url);
}