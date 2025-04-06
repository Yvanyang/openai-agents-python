"""Main module for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os
import asyncio

from agents import Agent, Runner, trace

from .models import (
    VueComponent,
    ReactComponent,
    ConversionPlan,
    ConversionResult,
    ConversionReport,
    ConversionIssue,
    KnowledgeBase,
)
from .agents import (
    FileAnalysisAgent,
    ConversionPlanningAgent,
    CodeConversionAgent,
    ComparisonAgent,
    KnowledgeBaseManager,
)


class VueToReactConverter:
    """Main class for converting Vue components to React components."""
    
    def __init__(
        self,
        source_dir: str,
        destination_dir: str,
        batch_size: int = 5,
        knowledge_base_path: Optional[str] = None,
        max_fix_iterations: int = 3,
    ):
        """
        Initialize the Vue-to-React converter.
        
        Args:
            source_dir: Directory containing Vue components
            destination_dir: Directory to write React components to
            batch_size: Maximum number of components to convert in a batch
            knowledge_base_path: Optional path to a knowledge base file
            max_fix_iterations: Maximum number of fix iterations to perform
        """
        self.source_dir = source_dir
        self.destination_dir = destination_dir
        self.batch_size = batch_size
        self.knowledge_base_path = knowledge_base_path
        self.max_fix_iterations = max_fix_iterations
        
        self.file_analysis_agent = FileAnalysisAgent()
        self.conversion_planning_agent = ConversionPlanningAgent()
        self.knowledge_base_manager = KnowledgeBaseManager(knowledge_base_path)
        self.code_conversion_agent = None  # Will be initialized after knowledge base is loaded
        self.comparison_agent = ComparisonAgent()
        
        self.vue_components = []
        self.conversion_plan = None
        self.conversion_results = []
    
    async def initialize(self):
        """Initialize the converter by loading the knowledge base."""
        knowledge_base = await self.knowledge_base_manager.initialize(self.knowledge_base_path)
        
        self.code_conversion_agent = CodeConversionAgent(knowledge_base)
    
    async def analyze_source_directory(self):
        """
        Analyze the source directory and generate documentation.
        
        Returns:
            A list of VueComponent objects
        """
        with trace("Analyzing source directory"):
            analysis_result = await self.file_analysis_agent.analyze_directory(self.source_dir)
            self.vue_components = analysis_result.components
            
            docs_dir = os.path.join(self.destination_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            
            for file_path, doc in analysis_result.documentation.items():
                component_name = os.path.basename(file_path).split(".")[0]
                doc_path = os.path.join(docs_dir, f"{component_name}.md")
                
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(doc)
            
            return self.vue_components
    
    async def create_conversion_plan(self):
        """
        Create a conversion plan based on component dependencies.
        
        Returns:
            A ConversionPlan object
        """
        with trace("Creating conversion plan"):
            self.conversion_plan = await self.conversion_planning_agent.create_plan(
                self.vue_components, self.batch_size
            )
            
            plan_dir = os.path.join(self.destination_dir, "docs")
            os.makedirs(plan_dir, exist_ok=True)
            plan_path = os.path.join(plan_dir, "conversion_plan.md")
            
            with open(plan_path, "w", encoding="utf-8") as f:
                f.write("# Vue to React Conversion Plan\n\n")
                f.write(f"Total components: {len(self.vue_components)}\n")
                f.write(f"Batch size: {self.batch_size}\n")
                f.write(f"Total batches: {len(self.conversion_plan.batches)}\n\n")
                
                f.write("## Conversion Order\n\n")
                for i, file_path in enumerate(self.conversion_plan.conversion_order):
                    component_name = os.path.basename(file_path).split(".")[0]
                    f.write(f"{i+1}. {component_name} ({file_path})\n")
                
                f.write("\n## Batches\n\n")
                for i, batch in enumerate(self.conversion_plan.batches):
                    f.write(f"### Batch {i+1} (Priority: {batch.priority})\n\n")
                    for file_path in batch.files:
                        component_name = os.path.basename(file_path).split(".")[0]
                        f.write(f"- {component_name} ({file_path})\n")
                    f.write("\n")
            
            return self.conversion_plan
    
    async def convert_batch(self, batch_index: int):
        """
        Convert a batch of Vue components to React.
        
        Args:
            batch_index: Index of the batch to convert
            
        Returns:
            A list of ConversionResult objects
        """
        if not self.conversion_plan:
            raise ValueError("Conversion plan not created yet")
        
        batch = self.conversion_plan.batches[batch_index]
        batch_results = []
        
        with trace(f"Converting batch {batch_index+1}"):
            batch_components = []
            for file_path in batch.files:
                for component in self.vue_components:
                    if component.file_path == file_path:
                        batch_components.append(component)
                        break
            
            for component in batch_components:
                component_name = os.path.basename(component.file_path).split(".")[0]
                component_dir = os.path.join(self.destination_dir, "components", component_name)
                os.makedirs(component_dir, exist_ok=True)
                
                react_component = await self.code_conversion_agent.convert_component(
                    component, component_dir
                )
                
                comparison_result = await self.comparison_agent.compare_components(
                    component, react_component
                )
                
                fix_iterations = 0
                while (
                    not comparison_result.is_equivalent
                    and fix_iterations < self.max_fix_iterations
                    and comparison_result.issues
                ):
                    fix_dir = os.path.join(component_dir, f"fix_{fix_iterations+1}")
                    os.makedirs(fix_dir, exist_ok=True)
                    
                    fixed_component = await self._apply_fixes(
                        react_component, comparison_result.issues, fix_dir
                    )
                    
                    comparison_result = await self.comparison_agent.compare_components(
                        component, fixed_component
                    )
                    
                    react_component = fixed_component
                    
                    fix_iterations += 1
                
                result = ConversionResult(
                    original_file=component.file_path,
                    converted_file=react_component.file_path,
                    issues=comparison_result.issues,
                    fix_iterations=fix_iterations,
                    status="success" if comparison_result.is_equivalent else "partial" if fix_iterations > 0 else "failed",
                )
                
                batch_results.append(result)
        
        return batch_results
    
    async def _apply_fixes(
        self, react_component: ReactComponent, issues: List[ConversionIssue], output_dir: str
    ) -> ReactComponent:
        """
        Apply fixes to a React component based on identified issues.
        
        Args:
            react_component: The React component to fix
            issues: List of issues to fix
            output_dir: Directory to write the fixed component to
            
        Returns:
            The fixed React component
        """
        fixed_component = ReactComponent(
            name=react_component.name,
            imports=react_component.imports.copy(),
            props=react_component.props.copy(),
            state=react_component.state.copy(),
            effects=react_component.effects.copy(),
            methods=react_component.methods.copy(),
            jsx=react_component.jsx,
            css=react_component.css,
            file_path="",  # Will be set when writing the component
        )
        
        for issue in issues:
            if issue.suggested_fix:
                if issue.type == "missing_prop":
                    prop_name = issue.description.split("'")[1]
                    
                    fixed_component.props[prop_name] = {"type": "PropTypes.any"}
                
                elif issue.type == "missing_state":
                    state_name = issue.description.split("'")[1]
                    
                    fixed_component.state[state_name] = "null"
                
                elif issue.type == "missing_method":
                    method_name = issue.description.split("'")[1]
                    
                    fixed_component.methods[method_name] = "// TODO: Implement this method"
                
                elif issue.type == "missing_lifecycle_hook":
                    hook_name = issue.description.split("'")[1]
                    
                    fixed_component.effects.append({
                        "implementation": "// TODO: Implement this lifecycle hook",
                        "dependencies": "[]",
                    })
                
                elif issue.type == "missing_elements" or issue.type == "missing_conditional" or issue.type == "missing_list_rendering" or issue.type == "missing_event_handler":
                    fixed_component.jsx = f"// TODO: Fix issue: {issue.description}\n{fixed_component.jsx}"
        
        await self.code_conversion_agent.write_react_component(fixed_component, output_dir)
        
        return fixed_component
    
    async def convert_all(self):
        """
        Convert all Vue components to React.
        
        Returns:
            A ConversionReport object
        """
        if not self.conversion_plan:
            raise ValueError("Conversion plan not created yet")
        
        all_results = []
        
        with trace("Converting all components"):
            for i in range(len(self.conversion_plan.batches)):
                batch_results = await self.convert_batch(i)
                all_results.extend(batch_results)
        
        report = ConversionReport(
            total_files=len(all_results),
            successful_conversions=sum(1 for r in all_results if r.status == "success"),
            partial_conversions=sum(1 for r in all_results if r.status == "partial"),
            failed_conversions=sum(1 for r in all_results if r.status == "failed"),
            conversion_results=all_results,
            attention_areas=self._identify_attention_areas(all_results),
        )
        
        report_dir = os.path.join(self.destination_dir, "docs")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "conversion_report.md")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Vue to React Conversion Report\n\n")
            f.write(f"Total files: {report.total_files}\n")
            f.write(f"Successful conversions: {report.successful_conversions}\n")
            f.write(f"Partial conversions: {report.partial_conversions}\n")
            f.write(f"Failed conversions: {report.failed_conversions}\n\n")
            
            f.write("## Attention Areas\n\n")
            for area in report.attention_areas:
                f.write(f"### {area['name']}\n\n")
                f.write(f"{area['description']}\n\n")
                f.write("Affected components:\n\n")
                for component in area["components"]:
                    f.write(f"- {component}\n")
                f.write("\n")
            
            f.write("## Conversion Results\n\n")
            for result in report.conversion_results:
                component_name = os.path.basename(result.original_file).split(".")[0]
                f.write(f"### {component_name}\n\n")
                f.write(f"Status: {result.status}\n")
                f.write(f"Original file: {result.original_file}\n")
                f.write(f"Converted file: {result.converted_file}\n")
                f.write(f"Fix iterations: {result.fix_iterations}\n\n")
                
                if result.issues:
                    f.write("Issues:\n\n")
                    for issue in result.issues:
                        f.write(f"- **{issue.type}** ({issue.severity}): {issue.description}\n")
                        if issue.suggested_fix:
                            f.write(f"  - Suggested fix: {issue.suggested_fix}\n")
                    f.write("\n")
        
        self.conversion_results = all_results
        return report
    
    def _identify_attention_areas(self, results: List[ConversionResult]) -> List[Dict]:
        """
        Identify areas that need special attention after conversion.
        
        Args:
            results: List of conversion results
            
        Returns:
            A list of attention areas
        """
        attention_areas = []
        
        issue_types = {}
        for result in results:
            for issue in result.issues:
                if issue.type not in issue_types:
                    issue_types[issue.type] = []
                
                component_name = os.path.basename(result.original_file).split(".")[0]
                if component_name not in issue_types[issue.type]:
                    issue_types[issue.type].append(component_name)
        
        for issue_type, components in issue_types.items():
            if len(components) >= 3:  # If at least 3 components have this issue
                attention_areas.append({
                    "name": f"Common issue: {issue_type}",
                    "description": f"Multiple components have issues of type '{issue_type}'",
                    "components": components,
                })
        
        component_issues = {}
        for result in results:
            component_name = os.path.basename(result.original_file).split(".")[0]
            component_issues[component_name] = len(result.issues)
        
        problematic_components = [
            name for name, count in component_issues.items() if count >= 5
        ]
        if problematic_components:
            attention_areas.append({
                "name": "Components with multiple issues",
                "description": "These components have 5 or more issues and may need manual review",
                "components": problematic_components,
            })
        
        failed_components = [
            os.path.basename(result.original_file).split(".")[0]
            for result in results
            if result.status == "failed"
        ]
        if failed_components:
            attention_areas.append({
                "name": "Failed conversions",
                "description": "These components could not be converted successfully and need manual conversion",
                "components": failed_components,
            })
        
        return attention_areas
    
    async def run(self):
        """
        Run the entire conversion process.
        
        Returns:
            A ConversionReport object
        """
        with trace("Vue to React conversion"):
            await self.initialize()
            
            await self.analyze_source_directory()
            
            await self.create_conversion_plan()
            
            report = await self.convert_all()
            
            return report


async def convert_vue_to_react(
    source_dir: str,
    destination_dir: str,
    batch_size: int = 5,
    knowledge_base_path: Optional[str] = None,
    max_fix_iterations: int = 3,
):
    """
    Convert Vue components to React components.
    
    Args:
        source_dir: Directory containing Vue components
        destination_dir: Directory to write React components to
        batch_size: Maximum number of components to convert in a batch
        knowledge_base_path: Optional path to a knowledge base file
        max_fix_iterations: Maximum number of fix iterations to perform
        
    Returns:
        A ConversionReport object
    """
    converter = VueToReactConverter(
        source_dir=source_dir,
        destination_dir=destination_dir,
        batch_size=batch_size,
        knowledge_base_path=knowledge_base_path,
        max_fix_iterations=max_fix_iterations,
    )
    
    return await converter.run()
