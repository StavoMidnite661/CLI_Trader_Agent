document.addEventListener('DOMContentLoaded', () => {
    const ws = new WebSocket('ws://localhost:8766');

    const feedContainer = document.getElementById('feed');
    const positionsContainer = document.getElementById('positions');
    const pendingTradesContainer = document.getElementById('pending-trades');
    const totalPnlElement = document.getElementById('total-pnl');
    const pnlDeltaElement = document.getElementById('pnl-delta');

    ws.onopen = () => console.log('WebSocket connection established');
    ws.onclose = () => console.log('WebSocket connection closed');
    ws.onerror = (error) => console.error('WebSocket error:', error);

    ws.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('Received message:', message);

            switch (message.type) {
                case 'price':
                    renderPrice(message.data);
                    break;
                case 'position_update':
                    renderPositions(message.data);
                    break;
                case 'pnl_update':
                    renderPnl(message.data);
                    break;
                case 'pending_trade':
                    renderPendingTrade(message.data);
                    break;
                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

// Make every price tick feel like a heartbeat
function renderPrice(data) {
  const line = document.createElement('div');
  const change = ((data.asks[0].price - data.bids[0].price) / data.bids[0].price * 10000).toFixed(1);
  line.innerHTML = `
    <span style="color:#ffd700">[${new Date().toISOString().split('T')[1].split('.')[0]}]</span>
    <strong style="color:#ff0066">${data.instrument}</strong>
    BID <span style="color:#00ff99">${data.bids[0].price}</span>
    ASK <span style="color:#ff0066">${data.asks[0].price}</span>
    SPREAD ${change} pips
  `;
  document.getElementById('feed').prepend(line);
  // Limit to 150 lines
  if (document.getElementById('feed').children.length > 150)
    document.getElementById('feed').removeChild(document.getElementById('feed').lastChild);
}

    function renderPositions(positions) {
        if (!positions || positions.length === 0) {
            positionsContainer.innerHTML = 'NO POSITIONS — MARKET IS MY B*TCH';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Instrument</th>
                        <th>Units</th>
                        <th>Side</th>
                        <th>Entry Price</th>
                    </tr>
                </thead>
                <tbody>
                    ${positions.map(p => `
                        <tr>
                            <td>${p.instrument}</td>
                            <td>${p.units}</td>
                            <td>${p.side}</td>
                            <td>${p.entry_price}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        positionsContainer.innerHTML = table;
    }

    function renderPnl(pnl) {
        const totalPnl = (pnl.realized + pnl.unrealized).toFixed(2);
        totalPnlElement.textContent = `$${totalPnl}`;

        // Example delta calculation - replace with your own logic
        const delta = (Math.random() * 2 - 1).toFixed(2); // Random +/- 1%
        pnlDeltaElement.textContent = `${delta >= 0 ? '+' : ''}${delta}%`;
        pnlDeltaElement.style.color = delta >= 0 ? '#00ff99' : '#ff0066';
    }

    function renderPendingTrade(trade) {
        const tradeElement = document.createElement('div');
        tradeElement.className = 'event';
        tradeElement.id = `trade-${trade.id}`;
        tradeElement.innerHTML = `
            <p><strong>New Trade Signal:</strong></p>
            <p>Instrument: ${trade.instrument}</p>
            <p>Signal: ${trade.signal}</p>
            <p>Confidence: ${trade.confidence}</p>
            <button id="approve-${trade.id}">Approve Trade</button>
        `;
        pendingTradesContainer.prepend(tradeElement);

        document.getElementById(`approve-${trade.id}`).addEventListener('click', () => {
            approveTrade(trade.id);
        });
    }

    function approveTrade(tradeId) {
        console.log(`Approving trade ${tradeId}...`);
        ws.send(JSON.stringify({
            type: 'approve_trade',
            trade_id: tradeId
        }));

        const tradeElement = document.getElementById(`trade-${tradeId}`);
        if (tradeElement) {
            tradeElement.remove();
        }
    }
});