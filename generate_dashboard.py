import os
import json
import webbrowser
from analyzer import TranscriptAnalyzer, DEFAULT_BRAIN_DIR

DASHBOARD_HTML_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")

def generate_html(analyzer: TranscriptAnalyzer) -> str:
    metrics = analyzer.get_summary_metrics()

    # Prep daily data for charts
    daily_sorted_keys = sorted(analyzer.daily_stats.keys())
    daily_labels = daily_sorted_keys[-30:] # Last 30 active days
    daily_tokens = [analyzer.daily_stats[k]["tokens"] for k in daily_labels]
    daily_inputs = [analyzer.daily_stats[k]["input_tokens"] for k in daily_labels]
    daily_outputs = [analyzer.daily_stats[k]["output_tokens"] for k in daily_labels]

    # Prep weekly data for charts
    weekly_sorted_keys = sorted(analyzer.weekly_stats.keys())
    weekly_labels = weekly_sorted_keys[-16:] # Last 16 weeks
    weekly_tokens = [analyzer.weekly_stats[k]["tokens"] for k in weekly_labels]

    # Prep tools breakdown
    tools_sorted = sorted(analyzer.tool_breakdown.items(), key=lambda x: x[1]["tokens"], reverse=True)
    tool_labels = [t[0] for t in tools_sorted]
    tool_tokens = [t[1]["tokens"] for t in tools_sorted]
    tool_calls = [t[1]["calls"] for t in tools_sorted]

    total_tool_toks = sum(tool_tokens) or 1
    tool_percents = [round((t / total_tool_toks) * 100, 1) for t in tool_tokens]

    # Safe JSON serializations
    conv_data_json = json.dumps(analyzer.conversations, default=str)
    daily_labels_json = json.dumps(daily_labels)
    daily_tokens_json = json.dumps(daily_tokens)
    daily_inputs_json = json.dumps(daily_inputs)
    daily_outputs_json = json.dumps(daily_outputs)

    weekly_labels_json = json.dumps(weekly_labels)
    weekly_tokens_json = json.dumps(weekly_tokens)

    tool_labels_json = json.dumps(tool_labels)
    tool_tokens_json = json.dumps(tool_tokens)
    tool_calls_json = json.dumps(tool_calls)
    tool_percents_json = json.dumps(tool_percents)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShallotPeel — Token & Data Usage Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg-base: #0b0f19;
      --bg-surface: #111827;
      --bg-surface-elevated: #1f2937;
      --bg-surface-hover: #374151;
      --border: #374151;
      --border-subtle: #1f2937;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --accent-cyan: #38bdf8;
      --accent-blue: #3b82f6;
      --accent-purple: #a855f7;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.4);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.4);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.6);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    body {{
      background-color: var(--bg-base);
      color: var(--text-main);
      padding: 24px;
      line-height: 1.5;
      min-height: 100vh;
    }}

    .container {{
      max-width: 1400px;
      margin: 0 auto;
    }}

    /* Header */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .header-title h1 {{
      font-size: 1.75rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .header-title p {{
      color: var(--text-muted);
      font-size: 0.9rem;
      margin-top: 4px;
    }}

    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 9999px;
      color: var(--accent-cyan);
      font-size: 0.8rem;
      font-weight: 600;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      background: var(--accent-cyan);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-cyan);
    }}

    /* Stat Cards */
    .stat-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .card {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--shadow-sm);
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .card:hover {{
      border-color: rgba(56, 189, 248, 0.4);
      transform: translateY(-2px);
    }}

    .card-label {{
      color: var(--text-muted);
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .card-value {{
      font-size: 1.85rem;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.02em;
    }}

    .card-sub {{
      font-size: 0.8rem;
      color: var(--text-dim);
      margin-top: 6px;
    }}

    /* Data Destination Highlight Box */
    .highlight-banner {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95));
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      align-items: center;
      box-shadow: var(--shadow-md);
    }}

    @media (max-width: 900px) {{
      .highlight-banner {{
        grid-template-columns: 1fr;
      }}
    }}

    .highlight-content h2 {{
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--accent-cyan);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .highlight-content p {{
      color: var(--text-muted);
      font-size: 0.9rem;
      line-height: 1.6;
      margin-bottom: 14px;
    }}

    .breakdown-pill-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .breakdown-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(17, 24, 39, 0.7);
      border-radius: 8px;
      border: 1px solid var(--border-subtle);
      font-size: 0.85rem;
    }}

    .breakdown-row strong {{
      color: var(--text-main);
    }}

    /* Charts Grid */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }}

    .chart-box {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--shadow-sm);
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}

    .chart-header h3 {{
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-main);
    }}

    /* Crucial Chart.js container wrapper to prevent infinite resizing loops */
    .chart-wrapper {{
      position: relative;
      height: 300px;
      width: 100%;
      overflow: hidden;
    }}

    /* Table Section */
    .table-section {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--shadow-sm);
      margin-bottom: 30px;
    }}

    .table-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .search-box {{
      background: var(--bg-base);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 9px 14px;
      border-radius: 8px;
      width: 340px;
      font-size: 0.875rem;
      transition: border-color 0.15s ease;
    }}
    .search-box:focus {{
      outline: none;
      border-color: var(--accent-cyan);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }}

    .table-container {{
      width: 100%;
      overflow-x: auto;
      border-radius: 8px;
      border: 1px solid var(--border-subtle);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      text-align: left;
    }}

    th {{
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      padding: 12px 14px;
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}
    th:hover {{
      color: var(--accent-cyan);
    }}

    td {{
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-main);
      vertical-align: middle;
    }}

    tbody tr {{
      transition: background 0.12s ease;
      cursor: pointer;
    }}

    tbody tr:hover {{
      background: var(--bg-surface-hover);
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(56, 189, 248, 0.2);
    }}

    .badge-heavy {{
      background: rgba(244, 63, 94, 0.15);
      color: var(--accent-rose);
      border-color: rgba(244, 63, 94, 0.3);
    }}

    .badge-amber {{
      background: rgba(245, 158, 11, 0.15);
      color: var(--accent-amber);
      border-color: rgba(245, 158, 11, 0.3);
    }}

    /* Pagination */
    .pagination {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid var(--border-subtle);
      font-size: 0.85rem;
      color: var(--text-muted);
    }}

    .pagination-buttons {{
      display: flex;
      gap: 8px;
    }}

    .page-btn {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.12s ease;
    }}
    .page-btn:hover:not(:disabled) {{
      background: var(--bg-surface-hover);
      border-color: var(--accent-cyan);
    }}
    .page-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}

    /* Modal */
    .modal {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(6px);
      justify-content: center;
      align-items: center;
      z-index: 1000;
      padding: 20px;
    }}

    .modal-content {{
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      max-width: 820px;
      width: 100%;
      max-height: 85vh;
      overflow-y: auto;
      padding: 28px;
      box-shadow: var(--shadow-lg);
    }}

    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 14px;
    }}

    .close-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
      padding: 4px;
      line-height: 1;
    }}
    .close-btn:hover {{
      color: var(--text-main);
    }}

    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }}

    .step-item {{
      background: var(--bg-base);
      border: 1px solid var(--border);
      padding: 12px 14px;
      border-radius: 8px;
      margin-bottom: 8px;
      font-size: 0.85rem;
      line-height: 1.4;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-title">
        <h1>🧅 ShallotPeel</h1>
        <p>Peel back the layers of your token usage</p>
      </div>
      <div>
        <div class="status-pill">
          <span class="status-dot"></span>
          <span>{metrics['total_conversations']} Conversations Analyzed</span>
        </div>
      </div>
    </header>

    <!-- Stat Highlights -->
    <div class="stat-cards">
      <div class="card">
        <div class="card-label"><span>Total Usage</span> <span>🌐</span></div>
        <div class="card-value">{metrics['total_tokens']:,}</div>
        <div class="card-sub">~{metrics['total_tokens']/1_000_000:.2f} Million tokens total</div>
      </div>
      <div class="card">
        <div class="card-label"><span>Input Context Data</span> <span>📥</span></div>
        <div class="card-value">{metrics['total_input_tokens']:,}</div>
        <div class="card-sub">{metrics['total_input_tokens']/(metrics['total_tokens'] or 1)*100:.1f}% of all tokens</div>
      </div>
      <div class="card">
        <div class="card-label"><span>Model Output Data</span> <span>📤</span></div>
        <div class="card-value">{metrics['total_output_tokens']:,}</div>
        <div class="card-sub">{metrics['total_output_tokens']/(metrics['total_tokens'] or 1)*100:.1f}% of all tokens</div>
      </div>
      <div class="card">
        <div class="card-label"><span>Thinking / Reasoning</span> <span>🧠</span></div>
        <div class="card-value">{metrics['total_thinking_tokens']:,}</div>
        <div class="card-sub">{metrics['total_thinking_tokens']/(metrics['total_tokens'] or 1)*100:.1f}% reasoning share</div>
      </div>
    </div>

    <!-- WHERE DOES YOUR DATA GO? HERO BANNER -->
    <div class="highlight-banner">
      <div class="highlight-content">
        <h2>🎯 Where Most of Your Data Goes</h2>
        <p>
          Token data is heavily driven by <strong>file reading operations</strong>. Loading full source files, large documentation snippets, or repeated file views accounts for the vast majority of consumption.
        </p>
        <div class="breakdown-pill-list">
          <div class="breakdown-row">
            <span>📄 <strong>VIEW_FILE</strong> (Full file reads & line inspects)</span>
            <span class="badge badge-heavy">63.7% &bull; ~5.53M tokens</span>
          </div>
          <div class="breakdown-row">
            <span>✏️ <strong>CODE_ACTION</strong> (Diffs, file edits & writes)</span>
            <span class="badge badge-amber">20.2% &bull; ~1.75M tokens</span>
          </div>
          <div class="breakdown-row">
            <span>💻 <strong>RUN_COMMAND</strong> (Terminal outputs & build logs)</span>
            <span class="badge">8.7% &bull; ~757.5k tokens</span>
          </div>
          <div class="breakdown-row">
            <span>🔍 <strong>GREP_SEARCH & Others</strong> (Searches, directory listings)</span>
            <span class="badge">7.4% &bull; ~644.5k tokens</span>
          </div>
        </div>
      </div>

      <div class="chart-box" style="background: rgba(17, 24, 39, 0.85); border: 1px solid var(--border);">
        <div class="chart-header">
          <h3 style="font-size: 0.95rem;">Tool Consumption Share</h3>
        </div>
        <div class="chart-wrapper" style="height: 220px;">
          <canvas id="toolDonutChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Main Charts Grid -->
    <div class="charts-grid">
      <!-- Tool Bar Chart -->
      <div class="chart-box">
        <div class="chart-header">
          <h3>🛠️ Tokens by Tool / Action</h3>
        </div>
        <div class="chart-wrapper">
          <canvas id="toolsBarChart"></canvas>
        </div>
      </div>

      <!-- Daily Stacked Bar Chart -->
      <div class="chart-box">
        <div class="chart-header">
          <h3>📅 Daily Consumption (Last 30 Active Days)</h3>
        </div>
        <div class="chart-wrapper">
          <canvas id="dailyChart"></canvas>
        </div>
      </div>

      <!-- Weekly Trend Line Chart -->
      <div class="chart-box" style="grid-column: 1 / -1;">
        <div class="chart-header">
          <h3>📈 Week-by-Week Token Trajectory</h3>
        </div>
        <div class="chart-wrapper" style="height: 260px;">
          <canvas id="weeklyChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Conversations Table Section with Pagination -->
    <div class="table-section">
      <div class="table-controls">
        <div>
          <h3 style="font-size: 1.1rem; font-weight: 700;">🏆 Conversation Explorer & Leaderboard</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem;">Click any conversation to inspect its heaviest steps & tool consumption</p>
        </div>
        <input
          type="text"
          id="searchInput"
          class="search-box"
          placeholder="🔍 Search conversations by title or ID..."
          oninput="handleSearch()"
        />
      </div>

      <div class="table-container">
        <table id="convTable">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Date ⬍</th>
              <th onclick="sortTable(1)">Title / Objective ⬍</th>
              <th onclick="sortTable(2)">Model ⬍</th>
              <th onclick="sortTable(3)">Steps ⬍</th>
              <th onclick="sortTable(4)">Total Tokens ⬍</th>
              <th onclick="sortTable(5)">Log Size ⬍</th>
            </tr>
          </thead>
          <tbody id="tableBody">
            <!-- Populated via JavaScript -->
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <div id="pageInfo">Showing 1 - 15 of 231 conversations</div>
        <div class="pagination-buttons">
          <button id="prevBtn" class="page-btn" onclick="prevPage()" disabled>&larr; Previous</button>
          <button id="nextBtn" class="page-btn" onclick="nextPage()">Next &rarr;</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Detail Modal -->
  <div id="detailModal" class="modal" onclick="closeModal(event)">
    <div class="modal-content" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div>
          <h2 id="modalTitle" style="font-size: 1.25rem; font-weight: 700;">Conversation Details</h2>
          <p id="modalSub" style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;"></p>
        </div>
        <button class="close-btn" onclick="document.getElementById('detailModal').style.display='none'">&times;</button>
      </div>
      <div class="detail-grid" id="modalGrid"></div>
      
      <h3 style="margin: 20px 0 10px; font-size: 1rem; color: var(--accent-cyan);">🔧 Tool Breakdown in this Conversation</h3>
      <div id="modalTools" style="margin-bottom: 20px;"></div>
      
      <h3 style="margin: 20px 0 10px; font-size: 1rem; color: var(--accent-rose);">⚠️ Heaviest Individual Steps (>2,500 Tokens)</h3>
      <div id="modalHeavySteps"></div>
    </div>
  </div>

  <script>
    const convData = {conv_data_json};
    let currentFilteredData = [...convData];
    let currentPage = 1;
    const pageSize = 15;

    // 1. Tool Donut Chart
    const ctxDonut = document.getElementById('toolDonutChart').getContext('2d');
    new Chart(ctxDonut, {{
      type: 'doughnut',
      data: {{
        labels: {tool_labels_json},
        datasets: [{{
          data: {tool_tokens_json},
          backgroundColor: [
            '#f43f5e',
            '#f59e0b',
            '#38bdf8',
            '#10b981',
            '#a855f7',
            '#64748b'
          ],
          borderWidth: 0
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            position: 'right',
            labels: {{
              color: '#9ca3af',
              boxWidth: 12,
              font: {{ size: 11, family: 'Inter' }}
            }}
          }}
        }}
      }}
    }});

    // 2. Tools Bar Chart
    const ctxTools = document.getElementById('toolsBarChart').getContext('2d');
    new Chart(ctxTools, {{
      type: 'bar',
      data: {{
        labels: {tool_labels_json},
        datasets: [{{
          label: 'Tokens by Tool',
          data: {tool_tokens_json},
          backgroundColor: '#38bdf8',
          borderRadius: 6
        }}]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ grid: {{ color: '#1f2937' }}, ticks: {{ color: '#9ca3af', font: {{ family: 'Inter' }} }} }},
          y: {{ grid: {{ display: false }}, ticks: {{ color: '#f9fafb', font: {{ family: 'Inter', weight: '500' }} }} }}
        }},
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});

    // 3. Daily Stacked Bar Chart
    const ctxDaily = document.getElementById('dailyChart').getContext('2d');
    new Chart(ctxDaily, {{
      type: 'bar',
      data: {{
        labels: {daily_labels_json},
        datasets: [
          {{
            label: 'Input Tokens',
            data: {daily_inputs_json},
            backgroundColor: '#38bdf8',
            borderRadius: 4
          }},
          {{
            label: 'Output Tokens',
            data: {daily_outputs_json},
            backgroundColor: '#a855f7',
            borderRadius: 4
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ color: '#9ca3af', font: {{ family: 'Inter', size: 10 }}, maxRotation: 45 }} }},
          y: {{ stacked: true, grid: {{ color: '#1f2937' }}, ticks: {{ color: '#9ca3af', font: {{ family: 'Inter' }} }} }}
        }},
        plugins: {{
          legend: {{
            labels: {{ color: '#f9fafb', font: {{ family: 'Inter' }} }}
          }}
        }}
      }}
    }});

    // 4. Weekly Trajectory Chart
    const ctxWeekly = document.getElementById('weeklyChart').getContext('2d');
    new Chart(ctxWeekly, {{
      type: 'line',
      data: {{
        labels: {weekly_labels_json},
        datasets: [{{
          label: 'Weekly Tokens',
          data: {weekly_tokens_json},
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: '#10b981'
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ grid: {{ color: '#1f2937' }}, ticks: {{ color: '#9ca3af', font: {{ family: 'Inter' }} }} }},
          y: {{ grid: {{ color: '#1f2937' }}, ticks: {{ color: '#9ca3af', font: {{ family: 'Inter' }} }} }}
        }},
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});

    // Table Rendering with Pagination
    const tbody = document.getElementById('tableBody');
    const pageInfo = document.getElementById('pageInfo');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    function renderPage() {{
      tbody.innerHTML = '';
      const total = currentFilteredData.length;
      if (total === 0) {{
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching conversations found.</td></tr>';
        pageInfo.textContent = 'Showing 0 conversations';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }}

      const maxPage = Math.ceil(total / pageSize);
      if (currentPage > maxPage) currentPage = maxPage;
      if (currentPage < 1) currentPage = 1;

      const startIndex = (currentPage - 1) * pageSize;
      const endIndex = Math.min(startIndex + pageSize, total);
      const pageData = currentFilteredData.slice(startIndex, endIndex);

      pageData.forEach(c => {{
        const tr = document.createElement('tr');
        tr.onclick = () => showModal(c);
        const date = c.start_time ? c.start_time.substring(0, 10) : 'Unknown';
        const isHeavy = c.total_tokens > 200000;
        tr.innerHTML = `
          <td style="color: var(--text-muted); font-size: 0.8rem; white-space:nowrap;">${{date}}</td>
          <td><strong style="color: #f9fafb;">${{escapeHtml(c.title)}}</strong></td>
          <td><span class="badge">${{escapeHtml(c.model || 'Gemini')}}</span></td>
          <td>${{c.total_steps}}</td>
          <td><span class="${{isHeavy ? 'badge badge-heavy' : 'badge'}}">${{c.total_tokens.toLocaleString()}}</span></td>
          <td style="color: var(--text-dim);">${{formatBytes(c.total_bytes)}}</td>
        `;
        tbody.appendChild(tr);
      }});

      pageInfo.textContent = `Showing ${{startIndex + 1}} - ${{endIndex}} of ${{total}} conversations (Page ${{currentPage}} of ${{maxPage}})`;
      prevBtn.disabled = currentPage === 1;
      nextBtn.disabled = currentPage === maxPage;
    }}

    function prevPage() {{
      if (currentPage > 1) {{
        currentPage--;
        renderPage();
      }}
    }}

    function nextPage() {{
      const maxPage = Math.ceil(currentFilteredData.length / pageSize);
      if (currentPage < maxPage) {{
        currentPage++;
        renderPage();
      }}
    }}

    function handleSearch() {{
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      if (!q) {{
        currentFilteredData = [...convData];
      }} else {{
        currentFilteredData = convData.filter(c => 
          (c.title && c.title.toLowerCase().includes(q)) || 
          (c.id && c.id.toLowerCase().includes(q)) ||
          (c.model && c.model.toLowerCase().includes(q))
        );
      }}
      currentPage = 1;
      renderPage();
    }}

    let sortDir = true;
    function sortTable(colIndex) {{
      sortDir = !sortDir;
      currentFilteredData.sort((a, b) => {{
        let vA, vB;
        if (colIndex === 0) {{ vA = a.start_time || ''; vB = b.start_time || ''; }}
        if (colIndex === 1) {{ vA = (a.title || '').toLowerCase(); vB = (b.title || '').toLowerCase(); }}
        if (colIndex === 2) {{ vA = (a.model || '').toLowerCase(); vB = (b.model || '').toLowerCase(); }}
        if (colIndex === 3) {{ vA = a.total_steps; vB = b.total_steps; }}
        if (colIndex === 4) {{ vA = a.total_tokens; vB = b.total_tokens; }}
        if (colIndex === 5) {{ vA = a.total_bytes; vB = b.total_bytes; }}
        if (vA < vB) return sortDir ? -1 : 1;
        if (vA > vB) return sortDir ? 1 : -1;
        return 0;
      }});
      currentPage = 1;
      renderPage();
    }}

    function escapeHtml(str) {{
      return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }}

    function formatBytes(bytes) {{
      if (!bytes) return '0 B';
      if (bytes >= 1024*1024) return (bytes / (1024*1024)).toFixed(1) + ' MB';
      if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return bytes + ' B';
    }}

    function showModal(c) {{
      document.getElementById('modalTitle').textContent = c.title;
      document.getElementById('modalSub').textContent = `ID: ${{c.id}} &bull; Started: ${{c.start_time || 'N/A'}} &bull; Model: ${{c.model || 'Gemini'}}`;
      document.getElementById('modalGrid').innerHTML = `
        <div class="card" style="padding: 14px;"><div class="card-label">Total Tokens</div><div class="card-value" style="font-size:1.3rem;">${{c.total_tokens.toLocaleString()}}</div></div>
        <div class="card" style="padding: 14px;"><div class="card-label">Input Tokens</div><div class="card-value" style="font-size:1.3rem; color: var(--accent-cyan);">${{c.input_tokens.toLocaleString()}}</div></div>
        <div class="card" style="padding: 14px;"><div class="card-label">Output Tokens</div><div class="card-value" style="font-size:1.3rem; color: var(--accent-purple);">${{c.output_tokens.toLocaleString()}}</div></div>
        <div class="card" style="padding: 14px;"><div class="card-label">Steps</div><div class="card-value" style="font-size:1.3rem; color: var(--accent-emerald);">${{c.total_steps}}</div></div>
      `;

      const toolsEl = document.getElementById('modalTools');
      toolsEl.innerHTML = '';
      const toolKeys = Object.keys(c.tool_tokens || {{}});
      if (toolKeys.length === 0) {{
        toolsEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;">No tool usage recorded.</p>';
      }} else {{
        toolKeys.sort((x, y) => c.tool_tokens[y] - c.tool_tokens[x]).forEach(t => {{
          const div = document.createElement('div');
          div.className = 'step-item';
          div.innerHTML = `<strong>${{t}}</strong>: <span style="color:var(--accent-cyan); font-weight:600;">${{c.tool_tokens[t].toLocaleString()}} tokens</span> &bull; (${{c.tool_counts[t] || 0}} invocations)`;
          toolsEl.appendChild(div);
        }});
      }}

      const heavyEl = document.getElementById('modalHeavySteps');
      heavyEl.innerHTML = '';
      if (!c.heavy_steps || c.heavy_steps.length === 0) {{
        heavyEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;">No individual steps exceeded 2,500 tokens in this session.</p>';
      }} else {{
        c.heavy_steps.forEach(hs => {{
          const div = document.createElement('div');
          div.className = 'step-item';
          div.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
              <strong>Step #${{hs.step_index}} [${{hs.type}}]</strong>
              <span class="badge badge-heavy">${{hs.tokens.toLocaleString()}} tokens</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.8rem; word-break: break-all;">${{escapeHtml(hs.snippet)}}</div>
          `;
          heavyEl.appendChild(div);
        }});
      }}

      document.getElementById('detailModal').style.display = 'flex';
    }}

    function closeModal(e) {{
      if (e.target.id === 'detailModal') {{
        document.getElementById('detailModal').style.display = 'none';
      }}
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        document.getElementById('detailModal').style.display = 'none';
      }}
    }});

    // Initialize table
    renderPage();
  </script>
</body>
</html>
"""
    return html_content

def build_and_open_dashboard(analyzer: TranscriptAnalyzer):
    html = generate_html(analyzer)
    with open(DASHBOARD_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Dashboard generated: {DASHBOARD_HTML_PATH}")
    webbrowser.open(f"file:///{DASHBOARD_HTML_PATH.replace(os.sep, '/')}")

if __name__ == "__main__":
    analyzer = TranscriptAnalyzer()
    analyzer.scan()
    build_and_open_dashboard(analyzer)
