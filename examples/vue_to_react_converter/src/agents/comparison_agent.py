"""Comparison agent for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os
import re

from agents import Agent, function_tool
from pydantic import BaseModel

from ..models import VueComponent, ReactComponent, ConversionIssue


class ComparisonResult(BaseModel):
    """Result of comparing a Vue component with its React conversion."""
    
    vue_component: VueComponent
    react_component: ReactComponent
    issues: List[ConversionIssue]
    is_equivalent: bool


class ComparisonAgent:
    """Agent for comparing Vue components with their React conversions."""
    
    def __init__(self):
        """Initialize the comparison agent."""
        self.agent = Agent(
            name="ComparisonAgent",
            instructions=(
                "You are a specialized agent for comparing Vue.js components with their React conversions. "
                "Your task is to analyze both components and determine if they are functionally equivalent, "
                "identifying any issues or discrepancies that need to be fixed."
            ),
            tools=[
                self.compare_props,
                self.compare_state_and_data,
                self.compare_methods,
                self.compare_lifecycle_hooks,
                self.compare_template_and_jsx,
                self.identify_issues,
                self.generate_comparison_report,
            ],
            model="gpt-4o",
        )
    
    @function_tool
    def compare_props(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Compare props between Vue and React components.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        for prop_name, prop_info in vue_component.props.items():
            if prop_name not in react_component.props:
                issues.append(
                    ConversionIssue(
                        type="missing_prop",
                        description=f"Prop '{prop_name}' is missing in React component",
                        location=f"Props definition in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add prop '{prop_name}' to React component",
                    )
                )
                continue
            
            vue_type = prop_info.get("type", "Any")
            react_type = react_component.props[prop_name].get("type", "Any")
            
            type_mapping = {
                "String": "string",
                "Number": "number",
                "Boolean": "bool",
                "Array": "array",
                "Object": "object",
                "Function": "func",
            }
            
            expected_react_type = type_mapping.get(vue_type, "any")
            
            if expected_react_type not in react_type.lower():
                issues.append(
                    ConversionIssue(
                        type="prop_type_mismatch",
                        description=f"Prop '{prop_name}' has type '{vue_type}' in Vue but '{react_type}' in React",
                        location=f"PropTypes definition in {react_component.name}",
                        severity="medium",
                        suggested_fix=f"Change prop type to '{expected_react_type}'",
                    )
                )
            
            vue_required = prop_info.get("required", False)
            react_required = "isRequired" in react_component.props[prop_name].get("type", "")
            
            if vue_required and not react_required:
                issues.append(
                    ConversionIssue(
                        type="prop_required_mismatch",
                        description=f"Prop '{prop_name}' is required in Vue but not in React",
                        location=f"PropTypes definition in {react_component.name}",
                        severity="medium",
                        suggested_fix=f"Add '.isRequired' to prop type",
                    )
                )
        
        for prop_name in react_component.props:
            if prop_name not in vue_component.props:
                issues.append(
                    ConversionIssue(
                        type="extra_prop",
                        description=f"Prop '{prop_name}' exists in React component but not in Vue component",
                        location=f"Props definition in {react_component.name}",
                        severity="low",
                        suggested_fix=f"Remove prop '{prop_name}' from React component if not needed",
                    )
                )
        
        return issues
    
    @function_tool
    def compare_state_and_data(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Compare data properties in Vue with state in React.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        for data_name, data_value in vue_component.data.items():
            if data_name not in react_component.state:
                issues.append(
                    ConversionIssue(
                        type="missing_state",
                        description=f"Data property '{data_name}' is missing in React state",
                        location=f"State definition in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add state '{data_name}' to React component with useState({data_value})",
                    )
                )
                continue
            
            vue_value = str(data_value).strip()
            react_value = str(react_component.state[data_name]).strip()
            
            vue_value = re.sub(r'\s+', '', vue_value)
            react_value = re.sub(r'\s+', '', react_value)
            
            if vue_value != react_value:
                issues.append(
                    ConversionIssue(
                        type="state_value_mismatch",
                        description=f"Data property '{data_name}' has value '{data_value}' in Vue but '{react_component.state[data_name]}' in React",
                        location=f"State definition in {react_component.name}",
                        severity="medium",
                        suggested_fix=f"Update initial state value to match Vue data property",
                    )
                )
        
        for state_name in react_component.state:
            if state_name in vue_component.computed:
                continue
                
            if state_name not in vue_component.data:
                issues.append(
                    ConversionIssue(
                        type="extra_state",
                        description=f"State '{state_name}' exists in React component but not in Vue component data",
                        location=f"State definition in {react_component.name}",
                        severity="low",
                        suggested_fix=f"Remove state '{state_name}' from React component if not needed",
                    )
                )
        
        return issues
    
    @function_tool
    def compare_methods(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Compare methods between Vue and React components.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        for method_name in vue_component.methods:
            if method_name not in react_component.methods:
                issues.append(
                    ConversionIssue(
                        type="missing_method",
                        description=f"Method '{method_name}' is missing in React component",
                        location=f"Methods in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add method '{method_name}' to React component",
                    )
                )
        
        for method_name in react_component.methods:
            if method_name.startswith('handle') or method_name.startswith('on'):
                continue
                
            if method_name not in vue_component.methods:
                issues.append(
                    ConversionIssue(
                        type="extra_method",
                        description=f"Method '{method_name}' exists in React component but not in Vue component",
                        location=f"Methods in {react_component.name}",
                        severity="low",
                        suggested_fix=f"Remove method '{method_name}' from React component if not needed",
                    )
                )
        
        return issues
    
    @function_tool
    def compare_lifecycle_hooks(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Compare lifecycle hooks in Vue with effects in React.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        lifecycle_mapping = {
            "created": "[]",  # Run once on mount
            "mounted": "[]",  # Run once on mount
            "updated": None,  # Run on every update
            "beforeDestroy": "[]",  # Run once on unmount with cleanup function
            "destroyed": "[]",  # Run once on unmount with cleanup function
        }
        
        for hook_name in vue_component.lifecycle_hooks:
            if hook_name in lifecycle_mapping:
                expected_deps = lifecycle_mapping[hook_name]
                
                found_matching_effect = False
                
                for effect in react_component.effects:
                    if expected_deps is None or effect.get("dependencies") == expected_deps:
                        found_matching_effect = True
                        break
                
                if not found_matching_effect:
                    issues.append(
                        ConversionIssue(
                            type="missing_lifecycle_hook",
                            description=f"Lifecycle hook '{hook_name}' is missing in React component",
                            location=f"Effects in {react_component.name}",
                            severity="high",
                            suggested_fix=f"Add useEffect for '{hook_name}' lifecycle hook",
                        )
                    )
        
        return issues
    
    @function_tool
    def compare_template_and_jsx(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Compare Vue template with React JSX.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        vue_elements = re.findall(r'<([a-zA-Z0-9_-]+)[^>]*>', vue_component.template)
        
        react_elements = re.findall(r'<([a-zA-Z0-9_-]+)[^>]*>', react_component.jsx)
        
        vue_elements_normalized = []
        for element in vue_elements:
            if "-" in element:
                parts = element.split("-")
                pascal_case = "".join(part.capitalize() for part in parts)
                vue_elements_normalized.append(pascal_case)
            else:
                vue_elements_normalized.append(element)
        
        vue_element_counts = {}
        for element in vue_elements_normalized:
            vue_element_counts[element] = vue_element_counts.get(element, 0) + 1
        
        react_element_counts = {}
        for element in react_elements:
            react_element_counts[element] = react_element_counts.get(element, 0) + 1
        
        for element, count in vue_element_counts.items():
            react_count = react_element_counts.get(element, 0)
            
            if react_count < count:
                issues.append(
                    ConversionIssue(
                        type="missing_elements",
                        description=f"Element '{element}' appears {count} times in Vue template but only {react_count} times in React JSX",
                        location=f"JSX in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add missing '{element}' elements to React JSX",
                    )
                )
        
        v_if_directives = re.findall(r'v-if="([^"]+)"', vue_component.template)
        
        for directive in v_if_directives:
            normalized_directive = re.sub(r'this\.', '', directive)
            
            if normalized_directive not in react_component.jsx and f"{normalized_directive} &&" not in react_component.jsx:
                issues.append(
                    ConversionIssue(
                        type="missing_conditional",
                        description=f"Conditional rendering 'v-if=\"{directive}\"' is missing in React JSX",
                        location=f"JSX in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add conditional rendering for '{normalized_directive}' to React JSX",
                    )
                )
        
        v_for_directives = re.findall(r'v-for="([^"]+)"', vue_component.template)
        
        for directive in v_for_directives:
            if " in " in directive:
                _, collection = directive.split(" in ")
                collection = collection.strip()
                
                normalized_collection = re.sub(r'this\.', '', collection)
                
                if f"{normalized_collection}.map" not in react_component.jsx:
                    issues.append(
                        ConversionIssue(
                            type="missing_list_rendering",
                            description=f"List rendering 'v-for=\"{directive}\"' is missing in React JSX",
                            location=f"JSX in {react_component.name}",
                            severity="high",
                            suggested_fix=f"Add list rendering with '{normalized_collection}.map()' to React JSX",
                        )
                    )
        
        vue_events = re.findall(r'@(\w+)="([^"]+)"', vue_component.template)
        
        for event, handler in vue_events:
            react_event = f"on{event[0].upper()}{event[1:]}"
            
            method_name = handler.split("(")[0] if "(" in handler else handler
            
            if react_event not in react_component.jsx and method_name not in react_component.jsx:
                issues.append(
                    ConversionIssue(
                        type="missing_event_handler",
                        description=f"Event handler '@{event}=\"{handler}\"' is missing in React JSX",
                        location=f"JSX in {react_component.name}",
                        severity="high",
                        suggested_fix=f"Add event handler '{react_event}' to React JSX",
                    )
                )
        
        return issues
    
    @function_tool
    def identify_issues(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> List[ConversionIssue]:
        """
        Identify issues between Vue and React components.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A list of issues found during comparison
        """
        issues = []
        
        issues.extend(self.compare_props(vue_component, react_component))
        
        issues.extend(self.compare_state_and_data(vue_component, react_component))
        
        issues.extend(self.compare_methods(vue_component, react_component))
        
        issues.extend(self.compare_lifecycle_hooks(vue_component, react_component))
        
        issues.extend(self.compare_template_and_jsx(vue_component, react_component))
        
        return issues
    
    @function_tool
    def generate_comparison_report(
        self, vue_component: VueComponent, react_component: ReactComponent, issues: List[ConversionIssue]
    ) -> ComparisonResult:
        """
        Generate a comparison report for Vue and React components.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            issues: List of issues found during comparison
            
        Returns:
            A ComparisonResult object
        """
        is_equivalent = True
        
        for issue in issues:
            if issue.severity == "high":
                is_equivalent = False
                break
        
        return ComparisonResult(
            vue_component=vue_component,
            react_component=react_component,
            issues=issues,
            is_equivalent=is_equivalent,
        )
    
    async def compare_components(
        self, vue_component: VueComponent, react_component: ReactComponent
    ) -> ComparisonResult:
        """
        Compare a Vue component with its React conversion.
        
        Args:
            vue_component: The original Vue component
            react_component: The converted React component
            
        Returns:
            A ComparisonResult object
        """
        from agents import Runner
        
        result = await Runner.run(
            self.agent,
            f"Identify issues between Vue component {vue_component.name} and React component {react_component.name}",
        )
        issues = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Generate a comparison report for Vue component {vue_component.name} and React component {react_component.name}",
        )
        comparison_result = result.final_output_as(ComparisonResult)
        
        return comparison_result
