"""
Web-based Database Viewer for Language Learning App
Provides a clean HTML interface to view database contents
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import os

# Create a separate Flask app for database viewing
db_app = Flask(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'db', 'language_app.db')

def get_database_info():
    """Get comprehensive database information"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        database_info = {
            'path': DB_PATH,
            'exists': os.path.exists(DB_PATH),
            'tables': {},
            'stats': {}
        }
        
        for table in tables:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]
            
            # Get sample data (first 50 rows)
            cursor.execute(f"SELECT * FROM {table} LIMIT 50;")
            rows = cursor.fetchall()
            
            database_info['tables'][table] = {
                'columns': columns,
                'row_count': row_count,
                'data': rows
            }
        
        conn.close()
        return database_info
        
    except Exception as e:
        return {'error': str(e), 'path': DB_PATH, 'exists': False}

@db_app.route('/')
def database_viewer():
    """Main database viewer page"""
    db_info = get_database_info()
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Language Learning App - Database Viewer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(45deg, #2c3e50, #34495e);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .db-info {
                background: #f8f9fa;
                padding: 20px;
                border-bottom: 1px solid #e9ecef;
            }
            
            .db-info h2 {
                color: #2c3e50;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
            }
            
            .status-online { background: #27ae60; }
            .status-offline { background: #e74c3c; }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .info-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            
            .table-nav {
                background: #2c3e50;
                padding: 0;
                overflow-x: auto;
            }
            
            .table-nav ul {
                display: flex;
                list-style: none;
                margin: 0;
                padding: 0;
                min-width: max-content;
            }
            
            .table-nav li {
                flex: 1;
            }
            
            .table-nav button {
                width: 100%;
                padding: 15px 25px;
                background: transparent;
                color: white;
                border: none;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 16px;
                border-right: 1px solid #34495e;
            }
            
            .table-nav button:hover,
            .table-nav button.active {
                background: #3498db;
                transform: translateY(-2px);
            }
            
            .table-content {
                padding: 30px;
                min-height: 400px;
            }
            
            .table-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #3498db;
            }
            
            .table-title {
                font-size: 1.8em;
                color: #2c3e50;
                font-weight: 600;
            }
            
            .row-count {
                background: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 500;
            }
            
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .data-table th {
                background: #34495e;
                color: white;
                padding: 15px 12px;
                text-align: left;
                font-weight: 600;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            .data-table td {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
                vertical-align: top;
            }
            
            .data-table tr:nth-child(even) {
                background: #f8f9fa;
            }
            
            .data-table tr:hover {
                background: #e3f2fd;
                transition: background 0.2s;
            }
            
            .column-info {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            
            .column-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }
            
            .column-item {
                background: white;
                padding: 10px;
                border-radius: 6px;
                border-left: 4px solid #3498db;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }
            
            .json-data {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .error-message {
                background: #ffe6e6;
                color: #c0392b;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e74c3c;
                margin: 20px;
            }
            
            .refresh-btn {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                margin-left: 15px;
                transition: all 0.3s;
            }
            
            .refresh-btn:hover {
                background: #229954;
                transform: translateY(-1px);
            }
            
            .no-data {
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                padding: 40px;
                font-size: 18px;
            }
            
            .scroll-container {
                max-height: 600px;
                overflow: auto;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            
            /* DANGEROUS DATABASE CLEARING SECTION */
            .danger-zone {
                background: linear-gradient(135deg, #ff4757, #ff3838);
                color: white;
                margin: 20px;
                border-radius: 12px;
                padding: 25px;
                border: 3px solid #ff1e1e;
                box-shadow: 0 0 20px rgba(255, 71, 87, 0.3);
            }
            
            .danger-zone h2 {
                color: white;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                font-size: 1.8em;
            }
            
            .danger-warning {
                background: rgba(255,255,255,0.2);
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                border-left: 5px solid #ffd700;
            }
            
            .clear-btn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: all 0.3s;
                margin: 10px 5px;
                border: 2px solid transparent;
            }
            
            .clear-btn:hover {
                background: #c0392b;
                border-color: #ffd700;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
            }
            
            .clear-btn:disabled {
                background: #bdc3c7;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .confirmation-step {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                border: 2px solid transparent;
            }
            
            .confirmation-step.completed {
                border-color: #27ae60;
                background: rgba(39, 174, 96, 0.2);
            }
            
            .confirmation-checkbox {
                margin-right: 10px;
                transform: scale(1.2);
            }
            
            .password-input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 2px solid #fff;
                border-radius: 6px;
                font-size: 16px;
                background: rgba(255,255,255,0.9);
            }
            
            .final-warning {
                background: #2c3e50;
                color: #e74c3c;
                padding: 20px;
                border-radius: 8px;
                margin: 15px 0;
                text-align: center;
                font-weight: bold;
                font-size: 18px;
                border: 3px dashed #e74c3c;
            }
            
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }
            
            .modal.active {
                display: flex;
            }
            
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 12px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                position: relative;
            }
            
            .modal-close {
                position: absolute;
                top: 15px;
                right: 20px;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🗄️ Database Viewer</h1>
                <p>Language Learning App - Real-time Database Content</p>
            </div>
            
            <div class="db-info">
                <h2>
                    <div class="status-indicator {{ 'status-online' if db_info.get('exists') else 'status-offline' }}"></div>
                    Database Status
                    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                </h2>
                
                <div class="info-grid">
                    <div class="info-card">
                        <strong>Database Path:</strong><br>
                        <code>{{ db_info.get('path', 'Unknown') }}</code>
                    </div>
                    <div class="info-card">
                        <strong>Status:</strong><br>
                        {{ 'Connected ✅' if db_info.get('exists') else 'Not Found ❌' }}
                    </div>
                    <div class="info-card">
                        <strong>Tables:</strong><br>
                        {{ db_info.get('tables', {}).keys() | length }} tables found
                    </div>
                    <div class="info-card">
                        <strong>Last Updated:</strong><br>
                        {{ current_time }}
                    </div>
                </div>
            </div>
            
            {% if db_info.get('error') %}
                <div class="error-message">
                    <h3>❌ Database Error</h3>
                    <p>{{ db_info.error }}</p>
                </div>
            {% else %}
                <nav class="table-nav">
                    <ul>
                        {% for table_name in db_info.get('tables', {}).keys() %}
                        <li>
                            <button onclick="showTable('{{ table_name }}')" 
                                    id="tab-{{ table_name }}" 
                                    class="{{ 'active' if loop.first else '' }}">
                                📊 {{ table_name.replace('_', ' ').title() }}
                            </button>
                        </li>
                        {% endfor %}
                    </ul>
                </nav>
                
                <div class="table-content">
                    {% for table_name, table_data in db_info.get('tables', {}).items() %}
                    <div id="table-{{ table_name }}" class="table-section" style="{{ 'display: block;' if loop.first else 'display: none;' }}">
                        <div class="table-header">
                            <h2 class="table-title">{{ table_name.replace('_', ' ').title() }}</h2>
                            <div class="row-count">{{ table_data.row_count }} rows</div>
                        </div>
                        
                        <div class="column-info">
                            <h3>📋 Table Structure</h3>
                            <div class="column-list">
                                {% for column in table_data.columns %}
                                <div class="column-item">
                                    <strong>{{ column[1] }}</strong><br>
                                    <small>{{ column[2] }}{{ ' (PK)' if column[5] else '' }}{{ ' NOT NULL' if column[3] else '' }}</small>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        {% if table_data.data %}
                        <div class="scroll-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        {% for column in table_data.columns %}
                                        <th>{{ column[1] }}</th>
                                        {% endfor %}
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for row in table_data.data %}
                                    <tr>
                                        {% for cell in row %}
                                        <td>
                                            {% if cell is none %}
                                                <em style="color: #999;">NULL</em>
                                            {% elif cell is string and (cell.startswith('{') or cell.startswith('[')) %}
                                                <div class="json-data" title="{{ cell }}">{{ cell }}</div>
                                            {% else %}
                                                {{ cell }}
                                            {% endif %}
                                        </td>
                                        {% endfor %}
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <div class="no-data">
                            📭 No data found in this table
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
        
        <!-- DANGEROUS DATABASE CLEARING SECTION -->
        <div class="danger-zone">
            <h2>⚠️ DANGER ZONE - DATABASE MANAGEMENT</h2>
            
            <div class="danger-warning">
                <strong>🚨 WARNING:</strong> The following actions are EXTREMELY DANGEROUS and will permanently delete ALL data from the database. This action cannot be undone!
            </div>
            
            <div class="danger-warning">
                <strong>📋 What will be deleted:</strong>
                <ul>
                    <li>All user accounts and profiles</li>
                    <li>All learning progress and XP data</li>
                    <li>All conversation history</li>
                    <li>All achievements and statistics</li>
                    <li>Every single record in the database</li>
                </ul>
            </div>
            
            <button class="clear-btn" onclick="showClearDatabaseModal()">
                🗑️ CLEAR ALL DATABASE DATA
            </button>
        </div>
        
        <!-- Database Clear Confirmation Modal -->
        <div id="clearDatabaseModal" class="modal">
            <div class="modal-content">
                <button class="modal-close" onclick="closeClearDatabaseModal()">&times;</button>
                <h2 style="color: #e74c3c;">⚠️ CONFIRM DATABASE DELETION</h2>
                
                <div class="final-warning">
                    THIS WILL DELETE EVERYTHING PERMANENTLY!<br>
                    NO RECOVERY IS POSSIBLE!
                </div>
                
                <div id="confirmationSteps">
                    <div class="confirmation-step" id="step1">
                        <label>
                            <input type="checkbox" class="confirmation-checkbox" id="confirm1" onchange="checkConfirmations()">
                            I understand this will delete ALL data permanently
                        </label>
                    </div>
                    
                    <div class="confirmation-step" id="step2">
                        <label>
                            <input type="checkbox" class="confirmation-checkbox" id="confirm2" onchange="checkConfirmations()">
                            I understand there is NO way to recover this data
                        </label>
                    </div>
                    
                    <div class="confirmation-step" id="step3">
                        <label>
                            <input type="checkbox" class="confirmation-checkbox" id="confirm3" onchange="checkConfirmations()">
                            I want to DELETE EVERYTHING in the database
                        </label>
                    </div>
                    
                    <div class="confirmation-step" id="step4">
                        <label for="adminPassword">Enter admin password to proceed:</label>
                        <input type="password" id="adminPassword" class="password-input" 
                               placeholder="Enter: CONFIRM_DELETE_ALL_DATA_2025" 
                               onchange="checkConfirmations()">
                    </div>
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <button class="clear-btn" id="finalDeleteBtn" onclick="executeDatabaseClear()" disabled>
                        💥 EXECUTE PERMANENT DELETION
                    </button>
                    <button class="clear-btn" style="background: #95a5a6;" onclick="closeClearDatabaseModal()">
                        ❌ Cancel (Safe Option)
                    </button>
                </div>
                
                <div id="clearingProgress" style="display: none;">
                    <h3>🔥 DELETING ALL DATA...</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <div style="font-size: 50px;">💀</div>
                        <p>This may take a moment...</p>
                    </div>
                </div>
                
                <div id="clearingResult" style="display: none;">
                    <!-- Results will be shown here -->
                </div>
            </div>
        </div>
        
        <script>
            function showTable(tableName) {
                // Hide all table sections
                const sections = document.querySelectorAll('.table-section');
                sections.forEach(section => section.style.display = 'none');
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.table-nav button');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected table and activate tab
                document.getElementById('table-' + tableName).style.display = 'block';
                document.getElementById('tab-' + tableName).classList.add('active');
            }
            
            // Database clearing functions
            function showClearDatabaseModal() {
                document.getElementById('clearDatabaseModal').classList.add('active');
                resetClearingModal();
            }
            
            function closeClearDatabaseModal() {
                document.getElementById('clearDatabaseModal').classList.remove('active');
                resetClearingModal();
            }
            
            function resetClearingModal() {
                // Reset all checkboxes
                document.getElementById('confirm1').checked = false;
                document.getElementById('confirm2').checked = false;
                document.getElementById('confirm3').checked = false;
                document.getElementById('adminPassword').value = '';
                
                // Reset button state
                document.getElementById('finalDeleteBtn').disabled = true;
                
                // Reset step styling
                document.querySelectorAll('.confirmation-step').forEach(step => {
                    step.classList.remove('completed');
                });
                
                // Hide progress and results
                document.getElementById('clearingProgress').style.display = 'none';
                document.getElementById('clearingResult').style.display = 'none';
                document.getElementById('confirmationSteps').style.display = 'block';
            }
            
            function checkConfirmations() {
                const confirm1 = document.getElementById('confirm1').checked;
                const confirm2 = document.getElementById('confirm2').checked;
                const confirm3 = document.getElementById('confirm3').checked;
                const password = document.getElementById('adminPassword').value;
                
                // Update step styling
                document.getElementById('step1').classList.toggle('completed', confirm1);
                document.getElementById('step2').classList.toggle('completed', confirm2);
                document.getElementById('step3').classList.toggle('completed', confirm3);
                document.getElementById('step4').classList.toggle('completed', password === 'CONFIRM_DELETE_ALL_DATA_2025');
                
                // Enable final button only if all conditions met
                const allConfirmed = confirm1 && confirm2 && confirm3 && password === 'CONFIRM_DELETE_ALL_DATA_2025';
                document.getElementById('finalDeleteBtn').disabled = !allConfirmed;
            }
            
            async function executeDatabaseClear() {
                // Show progress
                document.getElementById('confirmationSteps').style.display = 'none';
                document.getElementById('clearingProgress').style.display = 'block';
                
                try {
                    const response = await fetch('/api/clear-database', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            CLEAR_ALL_DATA: true,
                            I_UNDERSTAND_THIS_IS_PERMANENT: true,
                            DELETE_EVERYTHING_NOW: true,
                            admin_password: 'CONFIRM_DELETE_ALL_DATA_2025'
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Hide progress
                    document.getElementById('clearingProgress').style.display = 'none';
                    
                    // Show result
                    const resultDiv = document.getElementById('clearingResult');
                    
                    if (response.ok && result.success) {
                        resultDiv.innerHTML = `
                            <div style="background: #27ae60; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                                <h3>✅ DATABASE CLEARED SUCCESSFULLY</h3>
                                <p><strong>${result.total_rows_deleted}</strong> rows deleted from <strong>${result.tables_cleared.length}</strong> tables</p>
                                <div style="margin: 15px 0;">
                                    <h4>Tables Cleared:</h4>
                                    ${result.tables_cleared.map(t => `<p>📊 ${t.table}: ${t.rows_deleted} rows deleted</p>`).join('')}
                                </div>
                                <p><em>Completed at: ${new Date(result.timestamp).toLocaleString()}</em></p>
                                <button class="clear-btn" style="background: #3498db; margin-top: 15px;" onclick="location.reload()">
                                    🔄 Refresh Page
                                </button>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                                <h3>❌ ERROR CLEARING DATABASE</h3>
                                <p>${result.error || 'Unknown error occurred'}</p>
                                <button class="clear-btn" style="background: #3498db; margin-top: 15px;" onclick="closeClearDatabaseModal()">
                                    ← Go Back
                                </button>
                            </div>
                        `;
                    }
                    
                    resultDiv.style.display = 'block';
                    
                } catch (error) {
                    console.error('Error clearing database:', error);
                    
                    // Hide progress
                    document.getElementById('clearingProgress').style.display = 'none';
                    
                    // Show error
                    const resultDiv = document.getElementById('clearingResult');
                    resultDiv.innerHTML = `
                        <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                            <h3>❌ NETWORK ERROR</h3>
                            <p>Failed to connect to server: ${error.message}</p>
                            <button class="clear-btn" style="background: #3498db; margin-top: 15px;" onclick="closeClearDatabaseModal()">
                                ← Go Back
                            </button>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                }
            }
            
            // Auto-refresh every 30 seconds
            setTimeout(() => {
                location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template, 
                                db_info=db_info, 
                                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@db_app.route('/api/database-stats')
def database_stats():
    """API endpoint for database statistics"""
    db_info = get_database_info()
    
    stats = {
        'total_tables': len(db_info.get('tables', {})),
        'total_rows': sum(table.get('row_count', 0) for table in db_info.get('tables', {}).values()),
        'database_exists': db_info.get('exists', False),
        'last_updated': datetime.now().isoformat()
    }
    
    return jsonify(stats)

@db_app.route('/api/clear-database', methods=['POST'])
def clear_database():
    """DANGEROUS: Clear all data from database with extreme security"""
    try:
        data = request.json or {}
        
        # Multiple security checks
        required_confirmations = [
            'CLEAR_ALL_DATA',
            'I_UNDERSTAND_THIS_IS_PERMANENT', 
            'DELETE_EVERYTHING_NOW'
        ]
        
        # Check all confirmations
        for confirmation in required_confirmations:
            if data.get(confirmation) != True:
                return jsonify({
                    'error': f'Missing required confirmation: {confirmation}',
                    'required_confirmations': required_confirmations
                }), 400
        
        # Check password (must be exact)
        if data.get('admin_password') != 'CONFIRM_DELETE_ALL_DATA_2025':
            return jsonify({
                'error': 'Invalid admin password'
            }), 403
        
        # Check database exists
        if not os.path.exists(DB_PATH):
            return jsonify({'error': 'Database file not found'}), 404
        
        # Get current stats before deletion
        pre_deletion_info = get_database_info()
        
        # Connect and clear all tables
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all table names (except system tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        cleared_tables = []
        total_deleted_rows = 0
        
        # Clear each table
        for table in tables:
            # Count rows before deletion
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]
            
            # Delete all data
            cursor.execute(f"DELETE FROM {table};")
            
            cleared_tables.append({
                'table': table,
                'rows_deleted': row_count
            })
            total_deleted_rows += row_count
        
        # Reset auto-increment sequences
        cursor.execute("DELETE FROM sqlite_sequence;")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Log the dangerous operation
        print(f"🚨 DATABASE CLEARED: {total_deleted_rows} rows deleted from {len(cleared_tables)} tables")
        print(f"🕒 Time: {datetime.now()}")
        print(f"📊 Tables cleared: {[t['table'] for t in cleared_tables]}")
        
        return jsonify({
            'success': True,
            'message': 'Database completely cleared',
            'tables_cleared': cleared_tables,
            'total_rows_deleted': total_deleted_rows,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to clear database: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🗄️ Starting Database Viewer Web Interface...")
    print(f"📍 Database path: {DB_PATH}")
    
    # Use environment variable for port, with fallback
    port = int(os.environ.get('DB_VIEWER_PORT', 5001))
    print(f"🌐 Open in browser: http://localhost:{port}")
    print("=" * 50)
    
    db_app.run(host='0.0.0.0', port=port, debug=True)
