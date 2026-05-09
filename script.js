/**
 * EDGE PROTOCOL Frontend Script
 * Loads scan results from results.json and populates the table
 */

async function loadResults() {
    try {
        const response = await fetch('results.json?t=' + Date.now());
        
        if (!response.ok) {
            showMessage('No scan results yet. First scan will run at 9 AM IST on weekdays.', 'info');
            return;
        }
        
        const data = await response.json();
        
        // Update timestamp
        if (data.timestamp) {
            const date = new Date(data.timestamp);
            const formattedDate = date.toLocaleDateString('en-IN', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
            const formattedTime = date.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('timestamp').textContent = `${formattedDate} at ${formattedTime}`;
        }
        
        // Update count
        document.getElementById('count').textContent = data.count;
        
        // Populate table
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = '';
        
        if (data.count === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #999;">
                        📊 No stocks match the criteria today.<br>
                        <small>Check back tomorrow or run manually from GitHub Actions.</small>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Add stock rows
        data.stocks.forEach((stock, index) => {
            const row = document.createElement('tr');
            
            // Determine RSI color
            let rsiClass = '';
            if (stock.rsi < 55) rsiClass = 'rsi-low';
            else if (stock.rsi > 70) rsiClass = 'rsi-high';
            else rsiClass = 'rsi-mid';
            
            row.innerHTML = `
                <td class="col-symbol"><strong>${stock.symbol}</strong></td>
                <td class="col-price">₹${stock.price.toFixed(2)}</td>
                <td class="col-ema">${stock.ema_20.toFixed(2)}</td>
                <td class="col-ema">${stock.ema_50.toFixed(2)}</td>
                <td class="col-ema">${stock.ema_200.toFixed(2)}</td>
                <td class="col-rsi ${rsiClass}">${stock.rsi.toFixed(2)}</td>
                <td class="col-st">${stock.supertrend.toFixed(2)}</td>
                <td class="col-vol">${formatVolume(stock.volume)}</td>
            `;
            tbody.appendChild(row);
        });
        
        // Add CSS for RSI colors
        if (!document.getElementById('rsi-styles')) {
            const style = document.createElement('style');
            style.id = 'rsi-styles';
            style.textContent = `
                .rsi-low { color: #dc3545; font-weight: 600; }
                .rsi-mid { color: #667eea; font-weight: 600; }
                .rsi-high { color: #ffc107; font-weight: 600; }
            `;
            document.head.appendChild(style);
        }
    
    } catch (error) {
        console.error('Error loading results:', error);
        showMessage('Unable to load results. Check console for details.', 'error');
    }
}

function formatVolume(volume) {
    if (volume >= 1000000) {
        return (volume / 1000000).toFixed(1) + 'M';
    } else if (volume >= 1000) {
        return (volume / 1000).toFixed(1) + 'K';
    }
    return volume.toString();
}

function showMessage(message, type = 'info') {
    const tbody = document.getElementById('tbody');
    const iconMap = {
        'info': '📋',
        'error': '❌',
        'success': '✅'
    };
    
    tbody.innerHTML = `
        <tr>
            <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                ${iconMap[type]} ${message}
            </td>
        </tr>
    `;
}

// Auto-refresh every 5 minutes
function setupAutoRefresh() {
    // Refresh immediately on load
    loadResults();
    
    // Then refresh every 5 minutes
    setInterval(loadResults, 5 * 60 * 1000);
}

// Load on page ready
document.addEventListener('DOMContentLoaded', setupAutoRefresh);

// Also listen for visibility changes — refresh when tab becomes visible
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        loadResults();
    }
});
