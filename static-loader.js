
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
    