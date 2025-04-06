"""Data models for the Vue-to-React converter."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class VueComponent(BaseModel):
    """Represents a Vue component with its structure and properties."""
    
    name: str = Field(description="Name of the Vue component")
    template: str = Field(description="HTML template of the Vue component")
    script: str = Field(description="JavaScript/TypeScript code of the Vue component")
    style: Optional[str] = Field(None, description="CSS styles of the Vue component")
    props: Dict[str, Dict] = Field(default_factory=dict, description="Component props with their types and defaults")
    data: Dict[str, any] = Field(default_factory=dict, description="Component data properties")
    computed: Dict[str, str] = Field(default_factory=dict, description="Computed properties with their implementations")
    methods: Dict[str, str] = Field(default_factory=dict, description="Component methods with their implementations")
    lifecycle_hooks: Dict[str, str] = Field(default_factory=dict, description="Lifecycle hooks with their implementations")
    dependencies: List[str] = Field(default_factory=list, description="List of component dependencies")
    file_path: str = Field(description="Path to the Vue component file")


class ReactComponent(BaseModel):
    """Represents a React component converted from a Vue component."""
    
    name: str = Field(description="Name of the React component")
    imports: List[str] = Field(default_factory=list, description="Import statements for the React component")
    props: Dict[str, Dict] = Field(default_factory=dict, description="Component props with their types and defaults")
    state: Dict[str, any] = Field(default_factory=dict, description="Component state properties")
    effects: List[Dict] = Field(default_factory=list, description="useEffect hooks with their dependencies")
    methods: Dict[str, str] = Field(default_factory=dict, description="Component methods with their implementations")
    jsx: str = Field(description="JSX code for the React component")
    css: Optional[str] = Field(None, description="CSS styles for the React component")
    file_path: str = Field(description="Path to the React component file")


class ConversionIssue(BaseModel):
    """Represents an issue found during the conversion process."""
    
    type: str = Field(description="Type of issue (e.g., 'syntax', 'functionality', 'missing_feature')")
    description: str = Field(description="Description of the issue")
    location: str = Field(description="Location in the code where the issue was found")
    severity: str = Field(description="Severity of the issue ('low', 'medium', 'high')")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the issue")


class ConversionBatch(BaseModel):
    """Represents a batch of files to be converted together."""
    
    files: List[str] = Field(description="List of file paths in the batch")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Dependencies between files in the batch")
    priority: int = Field(description="Priority of the batch (lower number = higher priority)")


class ConversionPlan(BaseModel):
    """Represents a plan for converting Vue components to React."""
    
    batches: List[ConversionBatch] = Field(description="Batches of files to be converted")
    dependency_graph: Dict[str, List[str]] = Field(description="Graph of dependencies between all components")
    conversion_order: List[str] = Field(description="Order in which components should be converted")


class ConversionResult(BaseModel):
    """Represents the result of converting a Vue component to React."""
    
    original_file: str = Field(description="Path to the original Vue component file")
    converted_file: str = Field(description="Path to the converted React component file")
    issues: List[ConversionIssue] = Field(default_factory=list, description="Issues found during conversion")
    fix_iterations: int = Field(default=0, description="Number of fix iterations performed")
    status: str = Field(description="Status of the conversion ('success', 'partial', 'failed')")


class ConversionReport(BaseModel):
    """Represents a report of the entire conversion process."""
    
    total_files: int = Field(description="Total number of files processed")
    successful_conversions: int = Field(description="Number of successful conversions")
    partial_conversions: int = Field(description="Number of partial conversions")
    failed_conversions: int = Field(description="Number of failed conversions")
    conversion_results: List[ConversionResult] = Field(description="Results of individual conversions")
    attention_areas: List[Dict] = Field(description="Areas that need special attention after conversion")


class KnowledgeBaseRule(BaseModel):
    """Represents a rule in the knowledge base for Vue to React conversion."""
    
    pattern: str = Field(description="Pattern to match in Vue code")
    replacement: str = Field(description="Replacement pattern for React code")
    description: str = Field(description="Description of the rule")
    examples: Dict[str, str] = Field(default_factory=dict, description="Examples of before and after conversion")


class KnowledgeBase(BaseModel):
    """Represents a knowledge base for Vue to React conversion."""
    
    rules: List[KnowledgeBaseRule] = Field(description="List of conversion rules")
    lifecycle_mappings: Dict[str, str] = Field(description="Mappings from Vue lifecycle hooks to React equivalents")
    directive_mappings: Dict[str, str] = Field(description="Mappings from Vue directives to React equivalents")
    special_cases: Dict[str, Dict] = Field(description="Special cases that need custom handling")
