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

def generate_static_site():
    """Generate static files for GitHub Pages"""
    
    # Create output directory
    output_dir = "docs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Try to get data from dashboard, with fallback
    try:
        # Import dashboard only when we need it
        from web_dashboard import WebDashboard
        
        # Initialize dashboard to get data
        dashboard = WebDashboard()
        
        # Get all data
        print("📊 Fetching data from Google Sheets...")
        relevant_data, uncat_data = dashboard.get_all_data()
        all_data = relevant_data + uncat_data
        
        # Get stats
        stats = dashboard.get_stats()
        
        print(f"✅ Retrieved {len(all_data)} messages from Google Sheets")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch fresh data from Google Sheets: {e}")
        print("📄 Using existing data from docs/data.json if available...")
        
        # Try to load existing data
        existing_data_file = os.path.join(output_dir, "data.json")
        if os.path.exists("docs/data.json"):
            with open("docs/data.json", 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                all_data = existing_data.get('messages', [])
                stats = existing_data.get('stats', {
                    'total_messages': 0,
                    'relevant_jobs': 0,
                    'uncategorized': 0,
                    'today_count': 0
                })
            print(f"📊 Using existing data with {len(all_data)} messages")
        else:
            # Create sample data for demo
            print("🆕 Creating sample data for demonstration...")
            all_data = create_sample_data()
            stats = {
                'total_messages': len(all_data),
                'relevant_jobs': len([m for m in all_data if m.get('Category') == 'Relevant']),
                'uncategorized': len([m for m in all_data if m.get('Category') == 'Uncategorized']),
                'today_count': 0
            }
    
    # Generate data.json for client-side loading
    data_export = {
        'last_updated': datetime.now().isoformat(),
        'stats': stats,
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
    create_static_html(output_dir, data_export)
    
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

def create_sample_data():
    """Create sample data for demonstration when Google Sheets is not accessible"""
    sample_data = [
        {
            'Message ID': 'sample_001',
            'Source Group': 'Sample Jobs Channel',
            'Message Date': '2025-08-02',
            'Message Time': '10:30:00',
            'Full Message': '''🚀 Frontend Developer Position - Remote

Company: TechCorp
Experience: 0-2 Years (Freshers Welcome!)
Location: Remote/Bangalore

Skills Required:
• React.js, JavaScript, HTML, CSS
• Git, API Integration
• Good communication skills

Apply: https://techcorp.com/careers
Contact: hr@techcorp.com

#jobs #frontend #react #freshers #remote''',
            'Category': 'Relevant',
            'extracted_links': ['https://techcorp.com/careers'],
            'formatted_message': '''**🚀 Frontend Developer Position - Remote**

**Company:** TechCorp  
**Experience:** 0-2 Years (Freshers Welcome!)  
**Location:** Remote/Bangalore

**Skills Required:**
• React.js, JavaScript, HTML, CSS
• Git, API Integration  
• Good communication skills

**Apply:** https://techcorp.com/careers  
**Contact:** hr@techcorp.com

#jobs #frontend #react #freshers #remote'''
        },
        {
            'Message ID': 'sample_002',
            'Source Group': 'Fresher Jobs Hub',
            'Message Date': '2025-08-02',
            'Message Time': '09:15:00',
            'Full Message': '''💼 Python Developer Internship

Company: DataTech Solutions
Duration: 6 months with full-time conversion
Stipend: ₹25,000/month

Requirements:
- Basic Python knowledge
- Eager to learn Django/Flask
- No prior experience required

Apply here: https://datatech.careers/intern
Deadline: 15th August

#internship #python #django #freshers #bengaluru''',
            'Category': 'Relevant',
            'extracted_links': ['https://datatech.careers/intern'],
            'formatted_message': '''**💼 Python Developer Internship**

**Company:** DataTech Solutions  
**Duration:** 6 months with full-time conversion  
**Stipend:** ₹25,000/month

**Requirements:**
- Basic Python knowledge
- Eager to learn Django/Flask
- No prior experience required

**Apply here:** https://datatech.careers/intern  
**Deadline:** 15th August

#internship #python #django #freshers #bengaluru'''
        },
        {
            'Message ID': 'sample_003',
            'Source Group': 'Tech Opportunities',
            'Message Date': '2025-08-01',
            'Message Time': '16:45:00',
            'Full Message': '''📢 Senior Software Architect Position

Company: Enterprise Solutions Inc.
Experience: 8+ Years
Location: Mumbai

Looking for experienced architects with:
- System design expertise
- Team leadership experience
- Cloud platforms (AWS/Azure)

Apply: careers@enterprise.com
Salary: ₹30-45 LPA

#senior #architect #experienced #mumbai''',
            'Category': 'Uncategorized',
            'extracted_links': [],
            'formatted_message': '''**📢 Senior Software Architect Position**

**Company:** Enterprise Solutions Inc.  
**Experience:** 8+ Years  
**Location:** Mumbai

Looking for experienced architects with:
- System design expertise
- Team leadership experience
- Cloud platforms (AWS/Azure)

**Apply:** careers@enterprise.com  
**Salary:** ₹30-45 LPA

#senior #architect #experienced #mumbai'''
        }
    ]
    
    return sample_data

def create_static_html(output_dir, data_export):
    """Create static HTML files"""
    
    # Read the existing template
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        print("❌ Error: templates/index.html not found!")
        return

    # Render the template with the stats data
    template = Template(template_content)
    rendered_html = template.render(stats=data_export['stats'])

    # Add data loading script for static site
    static_script = f"""
    <script>
        let all_data = {json.dumps(data_export['messages'], indent=2)};
        let sources_data = {json.dumps(data_export['sources'], indent=2)};
        let last_updated = "{data_export['last_updated']}";
    </script>
    <script src="./static-loader.js"></script>
    """

    # Replace the dynamic script with the static one
    final_html = rendered_html.replace(
        '<script src="/static/js/dashboard.js"></script>', 
        static_script
    )

    # Save static index.html
    with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)

    # Create static-loader.js
    static_loader_content = """
    document.addEventListener('DOMContentLoaded', () => {
        // Update stats
        document.querySelector('.stats-card h3').textContent = stats.total_messages;
        document.querySelectorAll('.card h3')[1].textContent = stats.relevant_jobs;
        document.querySelectorAll('.card h3')[2].textContent = stats.uncategorized;
        document.querySelectorAll('.card h3')[3].textContent = stats.today_count;

        // Update last updated time
        const lastUpdated = new Date(last_updated);
        document.getElementById('lastUpdated').innerHTML = 
            `<i class="fas fa-clock"></i> Updated: ${lastUpdated.toLocaleString()}`;

        // Load sources and messages
        loadSourcesFromData(sources_data);
        loadMessagesFromData(all_data);
    });
    """
    with open(f"{output_dir}/static-loader.js", 'w', encoding='utf-8') as f:
        f.write(static_loader_content)

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