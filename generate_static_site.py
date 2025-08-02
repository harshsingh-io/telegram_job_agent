#!/usr/bin/env python3
"""
Static Site Generator for GitHub Pages
Converts dynamic dashboard to static files with JSON data
"""

import json
import os
import shutil
from datetime import datetime
from jinja2 import Template

# Import your existing dashboard
from web_dashboard import WebDashboard

def generate_static_site():
    """Generate static files for GitHub Pages"""
    
    # Create output directory
    output_dir = "docs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Initialize dashboard to get data
    dashboard = WebDashboard()
    
    # Get all data
    print("📊 Fetching data from Google Sheets...")
    relevant_data, uncat_data = dashboard.get_all_data()
    all_data = relevant_data + uncat_data
    
    # Generate data.json for client-side loading
    data_export = {
        'last_updated': datetime.now().isoformat(),
        'stats': dashboard.get_stats(),
        'messages': all_data,
        'sources': []
    }
    
    # Get sources with counts
    from collections import Counter
    source_counts = Counter([item.get('Source Group', 'Unknown') for item in all_data])
    data_export['sources'] = [
        {'name': source, 'count': count}
        for source, count in sorted(source_counts.items())
    ]
    
    # Save data.json
    with open(f"{output_dir}/data.json", 'w', encoding='utf-8') as f:
        json.dump(data_export, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated data.json with {len(all_data)} messages")
    
    # Create static HTML files
    create_static_html(output_dir, data_export['stats'])
    
    # Copy assets
    copy_assets(output_dir)
    
    # Create CNAME file for custom domain
    with open(f"{output_dir}/CNAME", 'w') as f:
        f.write("job.harshsingh.io")
    
    print(f"🎉 Static site generated in '{output_dir}' directory")
    print("📝 Next steps:")
    print("1. Commit and push the 'docs' folder to GitHub")
    print("2. Enable GitHub Pages in repository settings")
    print("3. Set source to 'docs' folder")
    print("4. Configure your domain DNS")

def create_static_html(output_dir, stats):
    """Create static HTML files"""
    
    # Read the existing template
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Create static version with JavaScript data loading
    static_html = template_content.replace(
        '{{ stats.total_messages }}', '0'
    ).replace(
        '{{ stats.relevant_jobs }}', '0'
    ).replace(
        '{{ stats.uncategorized }}', '0'
    ).replace(
        '{{ stats.today_count }}', '0'
    )
    
    # Add data loading script
    data_loading_script = """
    <script>
        // Load data from JSON file for GitHub Pages
        let globalData = null;
        
        async function loadDataFromJSON() {
            try {
                const response = await fetch('./data.json');
                globalData = await response.json();
                
                // Update stats
                document.querySelector('.stats-card h3').textContent = globalData.stats.total_messages;
                document.querySelectorAll('.card h3')[1].textContent = globalData.stats.relevant_jobs;
                document.querySelectorAll('.card h3')[2].textContent = globalData.stats.uncategorized;
                document.querySelectorAll('.card h3')[3].textContent = globalData.stats.today_count;
                
                // Update last updated time
                const lastUpdated = new Date(globalData.last_updated);
                document.getElementById('lastUpdated').innerHTML = 
                    `<i class="fas fa-clock"></i> Updated: ${lastUpdated.toLocaleString()}`;
                
                // Load sources and messages
                loadSourcesFromData();
                loadMessagesFromData();
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('messagesContainer').innerHTML = 
                    '<div class="alert alert-danger">Error loading data. Please try refreshing the page.</div>';
            }
        }
        
        function loadSourcesFromData() {
            const sourceDropdownMenu = document.getElementById("sourceDropdownMenu");
            
            // Clear existing items except "All Sources" and divider
            const existingItems = sourceDropdownMenu.querySelectorAll('li:not(:first-child):not(:nth-child(2))');
            existingItems.forEach(item => item.remove());

            globalData.sources.forEach((sourceData, index) => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <div class="dropdown-item">
                        <input class="form-check-input me-2 source-checkbox" type="checkbox" 
                               value="${sourceData.name}" id="source-${index}" 
                               onchange="updateSourceSelection()">
                        <label class="form-check-label" for="source-${index}">
                            ${sourceData.name} (${sourceData.count})
                        </label>
                    </div>
                `;
                sourceDropdownMenu.appendChild(li);
            });

            // Add event listener for "All Sources" checkbox
            document.getElementById('source-all').addEventListener('change', function() {
                if (this.checked) {
                    document.querySelectorAll('.source-checkbox').forEach(cb => cb.checked = false);
                }
                updateSourceSelection();
            });
        }
        
        function loadMessagesFromData() {
            if (!globalData) return;
            
            // Filter and display messages based on current filters
            const filteredData = filterMessages(globalData.messages);
            displayMessages(filteredData.slice(0, 20)); // Show first 20
        }
        
        function filterMessages(messages) {
            const category = document.getElementById("categoryFilter").value;
            const selectedSources = document.getElementById("selectedSources").value;
            const startDate = document.getElementById("startDate").value;
            const endDate = document.getElementById("endDate").value;
            const search = document.getElementById("searchInput").value.toLowerCase();
            
            let filtered = messages;
            
            // Category filter
            if (category === 'relevant') {
                filtered = filtered.filter(m => m.Category === 'Relevant');
            } else if (category === 'uncategorized') {
                filtered = filtered.filter(m => m.Category === 'Uncategorized');
            }
            
            // Source filter
            if (selectedSources !== 'all' && selectedSources) {
                const sources = selectedSources.split(',');
                filtered = filtered.filter(m => sources.includes(m['Source Group']));
            }
            
            // Date filter
            if (startDate && endDate) {
                filtered = filtered.filter(m => 
                    m['Message Date'] >= startDate && m['Message Date'] <= endDate
                );
            }
            
            // Search filter
            if (search) {
                filtered = filtered.filter(m => 
                    m['Full Message'].toLowerCase().includes(search) ||
                    m['Source Group'].toLowerCase().includes(search)
                );
            }
            
            // Sort by date (latest first)
            filtered.sort((a, b) => {
                const dateA = new Date(a['Message Date'] + ' ' + a['Message Time']);
                const dateB = new Date(b['Message Date'] + ' ' + b['Message Time']);
                return dateB - dateA;
            });
            
            return filtered;
        }
        
        // Override the original loadMessages function
        async function loadMessages() {
            if (!globalData) {
                await loadDataFromJSON();
                return;
            }
            
            const container = document.getElementById("messagesContainer");
            container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Filtering messages...</p></div>';
            
            setTimeout(() => {
                const filteredData = filterMessages(globalData.messages);
                displayMessages(filteredData.slice(0, parseInt(document.getElementById("perPageSelect").value)));
                document.getElementById("messageCount").textContent = filteredData.length;
            }, 100);
        }
        
        // Override API calls to use local data
        async function viewMessage(messageId) {
            if (!globalData) return;
            
            const message = globalData.messages.find(m => m['Message ID'] === messageId);
            if (message) {
                // Create a simple modal or new page
                const newWindow = window.open('', '_blank');
                newWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Message Details</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    </head>
                    <body>
                        <div class="container mt-4">
                            <h3>${message['Source Group']}</h3>
                            <p><strong>Date:</strong> ${message['Message Date']} ${message['Message Time']}</p>
                            <p><strong>Category:</strong> ${message.Category}</p>
                            <div class="card">
                                <div class="card-body">
                                    <pre style="white-space: pre-wrap;">${message['Full Message']}</pre>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                `);
            }
        }
        
        // Initialize when page loads
        document.addEventListener("DOMContentLoaded", function() {
            loadDataFromJSON();
            
            // Set default date range (last 7 days)
            const today = new Date();
            const weekAgo = new Date();
            weekAgo.setDate(today.getDate() - 7);
            
            document.getElementById("endDate").value = today.toISOString().split("T")[0];
            document.getElementById("startDate").value = weekAgo.toISOString().split("T")[0];
        });
    </script>
    """
    
    # Insert the script before closing body tag
    static_html = static_html.replace('</body>', data_loading_script + '\n</body>')
    
    # Save static index.html
    with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(static_html)

def copy_assets(output_dir):
    """Copy necessary assets"""
    
    # Create a simple 404 page
    html_404 = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found - Telegram Job Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5 text-center">
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/" class="btn btn-primary">Go Home</a>
        </div>
    </body>
    </html>
    """
    
    with open(f"{output_dir}/404.html", 'w') as f:
        f.write(html_404)
    
    # Create robots.txt
    robots_txt = """User-agent: *
Allow: /

Sitemap: https://job.harshsingh.io/sitemap.xml
"""
    
    with open(f"{output_dir}/robots.txt", 'w') as f:
        f.write(robots_txt)

if __name__ == "__main__":
    print("🚀 Generating static site for GitHub Pages...")
    generate_static_site()