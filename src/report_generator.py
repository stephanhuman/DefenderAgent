"""
Report generation for investigation results
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template


class ReportGenerator:
    """Generator for investigation reports"""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_json_report(
        self,
        investigation_results: List[Dict[str, Any]],
        report_type: str = "alerts"
    ) -> str:
        """
        Generate JSON report

        Args:
            investigation_results: List of investigation results
            report_type: Type of report (alerts or incidents)

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_investigation_{timestamp}.json"
        filepath = self.output_dir / filename

        report_data = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "total_items": len(investigation_results),
            "summary": self._generate_summary(investigation_results),
            "investigations": investigation_results
        }

        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)

        return str(filepath)

    def generate_html_report(
        self,
        investigation_results: List[Dict[str, Any]],
        report_type: str = "alerts"
    ) -> str:
        """
        Generate HTML report

        Args:
            investigation_results: List of investigation results
            report_type: Type of report (alerts or incidents)

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_investigation_{timestamp}.html"
        filepath = self.output_dir / filename

        template = self._get_html_template()
        summary = self._generate_summary(investigation_results)

        html_content = template.render(
            report_type=report_type,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_items=len(investigation_results),
            summary=summary,
            investigations=investigation_results
        )

        with open(filepath, 'w') as f:
            f.write(html_content)

        return str(filepath)

    def generate_markdown_report(
        self,
        investigation_results: List[Dict[str, Any]],
        report_type: str = "alerts"
    ) -> str:
        """
        Generate Markdown report

        Args:
            investigation_results: List of investigation results
            report_type: Type of report (alerts or incidents)

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_investigation_{timestamp}.md"
        filepath = self.output_dir / filename

        summary = self._generate_summary(investigation_results)

        lines = [
            f"# {report_type.title()} Investigation Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n**Total Items:** {len(investigation_results)}",
            "\n## Summary\n"
        ]

        # Add summary statistics
        lines.append(f"- **Critical Priority:** {summary['by_priority'].get('critical', 0)}")
        lines.append(f"- **High Priority:** {summary['by_priority'].get('high', 0)}")
        lines.append(f"- **Medium Priority:** {summary['by_priority'].get('medium', 0)}")
        lines.append(f"- **Low Priority:** {summary['by_priority'].get('low', 0)}")

        if report_type == "alerts" and summary.get('by_type'):
            lines.append("\n### By Alert Type\n")
            for alert_type, count in summary['by_type'].items():
                lines.append(f"- **{alert_type}:** {count}")

        # Add individual investigations
        lines.append("\n---\n\n## Investigation Details\n")

        for i, result in enumerate(investigation_results, 1):
            if report_type == "alerts":
                lines.append(f"### {i}. {result.get('alert_title', 'Unknown Alert')}\n")
                lines.append(f"- **Alert ID:** {result.get('alert_id', 'N/A')}")
                lines.append(f"- **Severity:** {result.get('severity', 'N/A').upper()}")
                lines.append(f"- **Priority:** {result.get('priority', 'N/A').upper()}")
                lines.append(f"- **Type:** {result.get('alert_type', 'N/A')}")
                lines.append(f"- **Status:** {result.get('investigation_status', 'N/A')}")
            else:
                lines.append(f"### {i}. {result.get('incident_name', 'Unknown Incident')}\n")
                lines.append(f"- **Incident ID:** {result.get('incident_id', 'N/A')}")
                lines.append(f"- **Severity:** {result.get('severity', 'N/A').upper()}")
                lines.append(f"- **Status:** {result.get('status', 'N/A')}")

            lines.append(f"\n**Investigation Report:**\n\n{result.get('investigation_report', 'No report available')}\n")
            lines.append("\n---\n")

        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        return str(filepath)

    def _generate_summary(self, investigation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            "total": len(investigation_results),
            "by_severity": {},
            "by_priority": {},
            "by_status": {},
            "by_type": {}
        }

        for result in investigation_results:
            # Count by severity
            severity = result.get("severity", "unknown")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

            # Count by priority
            priority = result.get("priority", "unknown")
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1

            # Count by status
            status = result.get("investigation_status", "unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

            # Count by type (for alerts)
            if "alert_type" in result:
                alert_type = result.get("alert_type", "unknown")
                summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1

        return summary

    def _get_html_template(self) -> Template:
        """Get HTML template for reports"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_type.title() }} Investigation Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .summary-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .investigation {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .investigation h3 {
            margin-top: 0;
            color: #333;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }
        .badge-critical { background: #dc3545; color: white; }
        .badge-high { background: #fd7e14; color: white; }
        .badge-medium { background: #ffc107; color: #333; }
        .badge-low { background: #28a745; color: white; }
        .badge-informational { background: #6c757d; color: white; }
        .report-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            white-space: pre-wrap;
        }
        .meta {
            color: #666;
            font-size: 0.9em;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_type.title() }} Investigation Report</h1>
        <p>Generated: {{ generated_at }}</p>
        <p>Total Items: {{ total_items }}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <strong>Critical Priority</strong><br>
                {{ summary.by_priority.get('critical', 0) }}
            </div>
            <div class="summary-item">
                <strong>High Priority</strong><br>
                {{ summary.by_priority.get('high', 0) }}
            </div>
            <div class="summary-item">
                <strong>Medium Priority</strong><br>
                {{ summary.by_priority.get('medium', 0) }}
            </div>
            <div class="summary-item">
                <strong>Low Priority</strong><br>
                {{ summary.by_priority.get('low', 0) }}
            </div>
        </div>
    </div>

    {% for investigation in investigations %}
    <div class="investigation">
        <h3>
            {% if investigation.alert_title %}
                {{ investigation.alert_title }}
            {% else %}
                {{ investigation.incident_name }}
            {% endif %}
        </h3>
        <div class="meta">
            {% if investigation.alert_id %}
                <strong>Alert ID:</strong> {{ investigation.alert_id }}<br>
            {% else %}
                <strong>Incident ID:</strong> {{ investigation.incident_id }}<br>
            {% endif %}
            <strong>Severity:</strong>
            <span class="badge badge-{{ investigation.severity }}">{{ investigation.severity|upper }}</span>
            <strong>Priority:</strong>
            <span class="badge badge-{{ investigation.priority }}">{{ investigation.priority|upper }}</span>
            {% if investigation.alert_type %}
                <strong>Type:</strong> {{ investigation.alert_type }}<br>
            {% endif %}
            <strong>Status:</strong> {{ investigation.investigation_status }}
        </div>
        <div class="report-content">{{ investigation.investigation_report }}</div>
    </div>
    {% endfor %}
</body>
</html>
        """
        return Template(template_str)
