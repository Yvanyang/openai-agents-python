"""Main module for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os
import asyncio
import logging
import sys
import time

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('vue_to_react_conversion.log')
    ]
)
logger = logging.getLogger('vue_to_react_converter')


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
        
        logger.info(f"Initializing Vue-to-React converter")
        logger.info(f"Source directory: {source_dir}")
        logger.info(f"Destination directory: {destination_dir}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Knowledge base path: {knowledge_base_path}")
        logger.info(f"Max fix iterations: {max_fix_iterations}")
        
        logger.info("Creating agents...")
        self.file_analysis_agent = FileAnalysisAgent()
        self.conversion_planning_agent = ConversionPlanningAgent()
        self.knowledge_base_manager = KnowledgeBaseManager(knowledge_base_path)
        self.code_conversion_agent = None  # Will be initialized after knowledge base is loaded
        self.comparison_agent = ComparisonAgent()
        logger.info("Agents created successfully")
        
        self.vue_components = []
        self.conversion_plan = None
        self.conversion_results = []
    
    async def initialize(self):
        """Initialize the converter by loading the knowledge base."""
        logger.info("Initializing converter and loading knowledge base...")
        start_time = time.time()
        
        knowledge_base = await self.knowledge_base_manager.initialize(self.knowledge_base_path)
        logger.info(f"Knowledge base loaded with {len(knowledge_base.rules)} rules")
        
        logger.info("Creating code conversion agent with knowledge base...")
        self.code_conversion_agent = CodeConversionAgent(knowledge_base)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Initialization completed in {elapsed_time:.2f} seconds")
    
    async def analyze_source_directory(self):
        """
        Analyze the source directory and generate documentation.
        
        Returns:
            A list of VueComponent objects
        """
        logger.info(f"Starting analysis of source directory: {self.source_dir}")
        start_time = time.time()
        
        with trace("Analyzing source directory"):
            logger.info("Invoking FileAnalysisAgent to analyze Vue components...")
            analysis_result = await self.file_analysis_agent.analyze_directory(self.source_dir)
            self.vue_components = analysis_result.components
            
            logger.info(f"Found {len(self.vue_components)} Vue components")
            for component in self.vue_components:
                logger.info(f"  - {component.name} ({component.file_path})")
                logger.info(f"    Props: {len(component.props)}, Methods: {len(component.methods)}, " +
                           f"Data: {len(component.data)}, Computed: {len(component.computed)}")
            
            logger.info("Generating documentation...")
            docs_dir = os.path.join(self.destination_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            
            for file_path, doc in analysis_result.documentation.items():
                component_name = os.path.basename(file_path).split(".")[0]
                doc_path = os.path.join(docs_dir, f"{component_name}.md")
                
                logger.info(f"Writing documentation for {component_name} to {doc_path}")
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(doc)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Source directory analysis completed in {elapsed_time:.2f} seconds")
            
            return self.vue_components
    
    async def create_conversion_plan(self):
        """
        Create a conversion plan based on component dependencies.
        
        Returns:
            A ConversionPlan object
        """
        logger.info("Creating conversion plan based on component dependencies...")
        start_time = time.time()
        
        with trace("Creating conversion plan"):
            logger.info(f"Invoking ConversionPlanningAgent to create plan for {len(self.vue_components)} components with batch size {self.batch_size}")
            self.conversion_plan = await self.conversion_planning_agent.create_plan(
                self.vue_components, self.batch_size
            )
            
            logger.info(f"Conversion plan created with {len(self.conversion_plan.batches)} batches")
            logger.info(f"Dependency graph contains {len(self.conversion_plan.dependency_graph)} components")
            
            logger.info("Conversion order:")
            for i, file_path in enumerate(self.conversion_plan.conversion_order):
                component_name = os.path.basename(file_path).split(".")[0]
                logger.info(f"  {i+1}. {component_name}")
            
            logger.info("Batches:")
            for i, batch in enumerate(self.conversion_plan.batches):
                logger.info(f"  Batch {i+1} (Priority: {batch.priority}) - {len(batch.files)} components")
                for file_path in batch.files:
                    component_name = os.path.basename(file_path).split(".")[0]
                    logger.info(f"    - {component_name}")
            
            logger.info("Writing conversion plan to file...")
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
            
            elapsed_time = time.time() - start_time
            logger.info(f"Conversion plan creation completed in {elapsed_time:.2f} seconds")
            
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
        
        logger.info(f"Starting conversion of batch {batch_index+1} (Priority: {batch.priority})")
        logger.info(f"Batch contains {len(batch.files)} components")
        start_time = time.time()
        
        with trace(f"Converting batch {batch_index+1}"):
            batch_components = []
            for file_path in batch.files:
                for component in self.vue_components:
                    if component.file_path == file_path:
                        batch_components.append(component)
                        break
            
            logger.info(f"Found {len(batch_components)} components to convert in this batch")
            
            for i, component in enumerate(batch_components):
                component_name = os.path.basename(component.file_path).split(".")[0]
                logger.info(f"Converting component {i+1}/{len(batch_components)}: {component_name}")
                component_start_time = time.time()
                
                component_dir = os.path.join(self.destination_dir, "components", component_name)
                os.makedirs(component_dir, exist_ok=True)
                logger.info(f"Created output directory: {component_dir}")
                
                logger.info(f"Invoking CodeConversionAgent to convert {component_name}...")
                react_component = await self.code_conversion_agent.convert_component(
                    component, component_dir
                )
                logger.info(f"Conversion completed for {component_name}")
                logger.info(f"React component created at {react_component.file_path}")
                
                logger.info(f"Comparing Vue and React versions of {component_name}...")
                comparison_result = await self.comparison_agent.compare_components(
                    component, react_component
                )
                
                if comparison_result.is_equivalent:
                    logger.info(f"Component {component_name} is functionally equivalent")
                else:
                    logger.info(f"Component {component_name} has {len(comparison_result.issues)} issues")
                    for issue in comparison_result.issues:
                        logger.info(f"  - {issue.type} ({issue.severity}): {issue.description}")
                
                fix_iterations = 0
                while (
                    not comparison_result.is_equivalent
                    and fix_iterations < self.max_fix_iterations
                    and comparison_result.issues
                ):
                    logger.info(f"Starting fix iteration {fix_iterations+1}/{self.max_fix_iterations} for {component_name}")
                    fix_dir = os.path.join(component_dir, f"fix_{fix_iterations+1}")
                    os.makedirs(fix_dir, exist_ok=True)
                    
                    logger.info(f"Applying fixes to {component_name}...")
                    fixed_component = await self._apply_fixes(
                        react_component, comparison_result.issues, fix_dir
                    )
                    
                    logger.info(f"Re-comparing Vue and fixed React versions of {component_name}...")
                    comparison_result = await self.comparison_agent.compare_components(
                        component, fixed_component
                    )
                    
                    if comparison_result.is_equivalent:
                        logger.info(f"Component {component_name} is now functionally equivalent after fix iteration {fix_iterations+1}")
                    else:
                        logger.info(f"Component {component_name} still has {len(comparison_result.issues)} issues after fix iteration {fix_iterations+1}")
                    
                    react_component = fixed_component
                    fix_iterations += 1
                
                status = "success" if comparison_result.is_equivalent else "partial" if fix_iterations > 0 else "failed"
                logger.info(f"Conversion status for {component_name}: {status}")
                
                result = ConversionResult(
                    original_file=component.file_path,
                    converted_file=react_component.file_path,
                    issues=comparison_result.issues,
                    fix_iterations=fix_iterations,
                    status=status,
                )
                
                batch_results.append(result)
                
                component_elapsed_time = time.time() - component_start_time
                logger.info(f"Component {component_name} conversion completed in {component_elapsed_time:.2f} seconds")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Batch {batch_index+1} conversion completed in {elapsed_time:.2f} seconds")
        logger.info(f"Batch results: {len(batch_results)} components processed")
        logger.info(f"  - Success: {sum(1 for r in batch_results if r.status == 'success')}")
        logger.info(f"  - Partial: {sum(1 for r in batch_results if r.status == 'partial')}")
        logger.info(f"  - Failed: {sum(1 for r in batch_results if r.status == 'failed')}")
        
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
        logger.info(f"Applying fixes to component {react_component.name}")
        logger.info(f"Number of issues to fix: {len(issues)}")
        logger.info(f"Output directory for fixed component: {output_dir}")
        start_time = time.time()
        
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
        
        for i, issue in enumerate(issues):
            logger.info(f"Fixing issue {i+1}/{len(issues)}: {issue.type} - {issue.description}")
            
            if issue.suggested_fix:
                logger.info(f"Applying suggested fix: {issue.suggested_fix}")
                
                if issue.type == "missing_prop":
                    prop_name = issue.description.split("'")[1]
                    logger.info(f"Adding missing prop: {prop_name}")
                    fixed_component.props[prop_name] = {"type": "PropTypes.any"}
                
                elif issue.type == "missing_state":
                    state_name = issue.description.split("'")[1]
                    logger.info(f"Adding missing state: {state_name}")
                    fixed_component.state[state_name] = "null"
                
                elif issue.type == "missing_method":
                    method_name = issue.description.split("'")[1]
                    logger.info(f"Adding missing method: {method_name}")
                    fixed_component.methods[method_name] = "// TODO: Implement this method"
                
                elif issue.type == "missing_lifecycle_hook":
                    hook_name = issue.description.split("'")[1]
                    logger.info(f"Adding missing lifecycle hook: {hook_name}")
                    fixed_component.effects.append({
                        "implementation": f"// TODO: Implement {hook_name} lifecycle hook",
                        "dependencies": "[]",
                    })
                
                elif issue.type in ["missing_elements", "missing_conditional", "missing_list_rendering", "missing_event_handler"]:
                    logger.info(f"Adding TODO comment for {issue.type}")
                    fixed_component.jsx = f"// TODO: Fix issue: {issue.description}\n{fixed_component.jsx}"
                
                else:
                    logger.warning(f"Unknown issue type: {issue.type}, no fix applied")
            else:
                logger.info(f"No suggested fix for issue {i+1}, skipping")
        
        logger.info(f"Writing fixed component to {output_dir}")
        await self.code_conversion_agent.write_react_component(fixed_component, output_dir)
        logger.info(f"Fixed component written to {fixed_component.file_path}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Fix application completed in {elapsed_time:.2f} seconds")
        
        return fixed_component
    
    async def convert_all(self):
        """
        Convert all Vue components to React.
        
        Returns:
            A ConversionReport object
        """
        if not self.conversion_plan:
            raise ValueError("Conversion plan not created yet")
        
        logger.info("Starting conversion of all components")
        logger.info(f"Total batches to process: {len(self.conversion_plan.batches)}")
        start_time = time.time()
        
        all_results = []
        
        with trace("Converting all components"):
            for i in range(len(self.conversion_plan.batches)):
                logger.info(f"Processing batch {i+1}/{len(self.conversion_plan.batches)}")
                batch_results = await self.convert_batch(i)
                all_results.extend(batch_results)
                logger.info(f"Batch {i+1} completed, {len(batch_results)} components processed")
        
        logger.info("All batches processed, generating conversion report")
        
        report = ConversionReport(
            total_files=len(all_results),
            successful_conversions=sum(1 for r in all_results if r.status == "success"),
            partial_conversions=sum(1 for r in all_results if r.status == "partial"),
            failed_conversions=sum(1 for r in all_results if r.status == "failed"),
            conversion_results=all_results,
            attention_areas=self._identify_attention_areas(all_results),
        )
        
        logger.info(f"Conversion report generated")
        logger.info(f"Total files: {report.total_files}")
        logger.info(f"Successful conversions: {report.successful_conversions}")
        logger.info(f"Partial conversions: {report.partial_conversions}")
        logger.info(f"Failed conversions: {report.failed_conversions}")
        logger.info(f"Attention areas identified: {len(report.attention_areas)}")
        
        logger.info("Writing conversion report to file")
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
        
        logger.info(f"Conversion report written to {report_path}")
        
        self.conversion_results = all_results
        
        elapsed_time = time.time() - start_time
        logger.info(f"All components conversion completed in {elapsed_time:.2f} seconds")
        
        return report
    
    def _identify_attention_areas(self, results: List[ConversionResult]) -> List[Dict]:
        """
        Identify areas that need special attention after conversion.
        
        Args:
            results: List of conversion results
            
        Returns:
            A list of attention areas
        """
        logger.info("Identifying attention areas from conversion results")
        start_time = time.time()
        
        attention_areas = []
        
        logger.info("Analyzing issue types across components")
        issue_types = {}
        for result in results:
            for issue in result.issues:
                if issue.type not in issue_types:
                    issue_types[issue.type] = []
                
                component_name = os.path.basename(result.original_file).split(".")[0]
                if component_name not in issue_types[issue.type]:
                    issue_types[issue.type].append(component_name)
        
        logger.info(f"Found {len(issue_types)} different issue types")
        for issue_type, components in issue_types.items():
            logger.info(f"  - {issue_type}: affects {len(components)} components")
            
            if len(components) >= 3:
                logger.info(f"  - Adding attention area for common issue: {issue_type}")
                attention_areas.append({
                    "name": f"Common issue: {issue_type}",
                    "description": f"Multiple components have issues of type '{issue_type}'",
                    "components": components,
                })
        
        logger.info("Analyzing components with multiple issues")
        component_issues = {}
        for result in results:
            component_name = os.path.basename(result.original_file).split(".")[0]
            component_issues[component_name] = len(result.issues)
            if len(result.issues) > 0:
                logger.info(f"  - {component_name}: {len(result.issues)} issues")
        
        problematic_components = [
            name for name, count in component_issues.items() if count >= 5
        ]
        if problematic_components:
            logger.info(f"Found {len(problematic_components)} components with 5+ issues")
            attention_areas.append({
                "name": "Components with multiple issues",
                "description": "These components have 5 or more issues and may need manual review",
                "components": problematic_components,
            })
        
        logger.info("Identifying failed conversions")
        failed_components = [
            os.path.basename(result.original_file).split(".")[0]
            for result in results
            if result.status == "failed"
        ]
        if failed_components:
            logger.info(f"Found {len(failed_components)} failed conversions")
            attention_areas.append({
                "name": "Failed conversions",
                "description": "These components could not be converted successfully and need manual conversion",
                "components": failed_components,
            })
        
        elapsed_time = time.time() - start_time
        logger.info(f"Attention area identification completed in {elapsed_time:.2f} seconds")
        logger.info(f"Identified {len(attention_areas)} attention areas")
        
        return attention_areas
    
    async def run(self):
        """
        Run the entire conversion process.
        
        Returns:
            A ConversionReport object
        """
        logger.info("Starting Vue to React conversion process")
        start_time = time.time()
        
        with trace("Vue to React conversion"):
            logger.info("Initializing converter...")
            await self.initialize()
            
            logger.info("Analyzing source directory...")
            await self.analyze_source_directory()
            
            logger.info("Creating conversion plan...")
            await self.create_conversion_plan()
            
            logger.info("Converting all components...")
            report = await self.convert_all()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Vue to React conversion process completed in {elapsed_time:.2f} seconds")
            logger.info(f"Conversion summary: {report.successful_conversions} successful, " +
                       f"{report.partial_conversions} partial, {report.failed_conversions} failed")
            
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
    logger.info("Starting Vue to React conversion")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Destination directory: {destination_dir}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Knowledge base path: {knowledge_base_path}")
    logger.info(f"Max fix iterations: {max_fix_iterations}")
    
    start_time = time.time()
    
    converter = VueToReactConverter(
        source_dir=source_dir,
        destination_dir=destination_dir,
        batch_size=batch_size,
        knowledge_base_path=knowledge_base_path,
        max_fix_iterations=max_fix_iterations,
    )
    
    logger.info("Created VueToReactConverter instance, starting conversion process")
    report = await converter.run()
    
    elapsed_time = time.time() - start_time
    logger.info(f"Vue to React conversion completed in {elapsed_time:.2f} seconds")
    logger.info(f"Conversion summary: {report.successful_conversions} successful, " +
               f"{report.partial_conversions} partial, {report.failed_conversions} failed")
    
    return report
