"""OpenMesh AI - Predefined Workflows"""

from typing import Dict, List, Any


class WorkflowTemplate:
    """Template for common workflows."""

    @staticmethod
    def job_application() -> List[Dict[str, Any]]:
        """Resume → Find Jobs → Tailor → Send → Track"""
        return [
            {
                "step": 1,
                "name": "parse_resume",
                "agent": "parser",
                "description": "Extract skills and experience from uploaded resume",
                "tools": ["pdf_reader", "file_reader"],
                "input_keys": ["resume_file"],
                "output_key": "resume_data"
            },
            {
                "step": 2,
                "name": "research_jobs",
                "agent": "research",
                "description": "Find matching job postings",
                "tools": ["browser", "github"],
                "input_keys": ["resume_data"],
                "output_key": "job_matches"
            },
            {
                "step": 3,
                "name": "research_company",
                "agent": "research",
                "description": "Deep research on target company",
                "tools": ["browser", "github"],
                "input_keys": ["job_matches"],
                "output_key": "company_research"
            },
            {
                "step": 4,
                "name": "tailor_resume",
                "agent": "writer",
                "description": "Customize resume for specific job",
                "tools": ["file_writer"],
                "input_keys": ["resume_data", "job_matches", "company_research"],
                "output_key": "tailored_resume"
            },
            {
                "step": 5,
                "name": "generate_cover_letter",
                "agent": "writer",
                "description": "Write personalized cover letter",
                "tools": ["file_writer"],
                "input_keys": ["resume_data", "job_matches", "company_research"],
                "output_key": "cover_letter"
            },
            {
                "step": 6,
                "name": "send_application",
                "agent": "communicator",
                "description": "Send application via email",
                "tools": ["gmail"],
                "input_keys": ["tailored_resume", "cover_letter", "job_matches"],
                "output_key": "send_status"
            },
            {
                "step": 7,
                "name": "track_application",
                "agent": "memory",
                "description": "Store application in tracking system",
                "tools": ["memory_store"],
                "input_keys": ["job_matches", "send_status"],
                "output_key": "tracking_id"
            }
        ]

    @staticmethod
    def code_review() -> List[Dict[str, Any]]:
        """PR → Analyze → Review → Comment"""
        return [
            {
                "step": 1,
                "name": "fetch_pr",
                "agent": "developer",
                "description": "Fetch PR diff from GitHub",
                "tools": ["github"],
                "input_keys": ["pr_url"],
                "output_key": "pr_diff"
            },
            {
                "step": 2,
                "name": "analyze_code",
                "agent": "reviewer",
                "description": "Analyze code quality and patterns",
                "tools": ["github", "browser"],
                "input_keys": ["pr_diff"],
                "output_key": "analysis"
            },
            {
                "step": 3,
                "name": "generate_review",
                "agent": "reviewer",
                "description": "Generate structured code review",
                "tools": [],
                "input_keys": ["pr_diff", "analysis"],
                "output_key": "review_comments"
            },
            {
                "step": 4,
                "name": "post_review",
                "agent": "developer",
                "description": "Post review to GitHub",
                "tools": ["github"],
                "input_keys": ["review_comments", "pr_url"],
                "output_key": "post_status"
            }
        ]

    @staticmethod
    def research_report() -> List[Dict[str, Any]]:
        """Topic → Search → Synthesize → Report"""
        return [
            {
                "step": 1,
                "name": "search_web",
                "agent": "research",
                "description": "Search web for information",
                "tools": ["browser"],
                "input_keys": ["topic"],
                "output_key": "search_results"
            },
            {
                "step": 2,
                "name": "search_github",
                "agent": "research",
                "description": "Search GitHub for repos and code",
                "tools": ["github"],
                "input_keys": ["topic"],
                "output_key": "github_results"
            },
            {
                "step": 3,
                "name": "synthesize",
                "agent": "writer",
                "description": "Synthesize findings into report",
                "tools": [],
                "input_keys": ["search_results", "github_results"],
                "output_key": "report"
            },
            {
                "step": 4,
                "name": "save_report",
                "agent": "memory",
                "description": "Save report to drive",
                "tools": ["gdrive"],
                "input_keys": ["report"],
                "output_key": "save_status"
            }
        ]


WORKFLOW_TEMPLATES = {
    "job_application": WorkflowTemplate.job_application,
    "code_review": WorkflowTemplate.code_review,
    "research_report": WorkflowTemplate.research_report,
}


def get_workflow_template(name: str) -> List[Dict[str, Any]]:
    """Get a workflow template by name."""
    if name not in WORKFLOW_TEMPLATES:
        raise ValueError(f"Unknown workflow: {name}. Available: {list(WORKFLOW_TEMPLATES.keys())}")
    return WORKFLOW_TEMPLATES[name]()
