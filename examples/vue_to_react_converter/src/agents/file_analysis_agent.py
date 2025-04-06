"""File analysis agent for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os
import re

from agents import Agent, function_tool
from pydantic import BaseModel

from ..models import VueComponent


class FileAnalysisResult(BaseModel):
    """Result of analyzing Vue files."""
    
    components: List[VueComponent]
    dependency_graph: Dict[str, List[str]]
    documentation: Dict[str, str]


class FileAnalysisAgent:
    """Agent for analyzing Vue files and generating documentation."""
    
    def __init__(self):
        """Initialize the file analysis agent."""
        self.agent = Agent(
            name="FileAnalysisAgent",
            instructions=(
                "You are a specialized agent for analyzing Vue.js files. "
                "Your task is to analyze Vue components, extract their structure, "
                "identify dependencies between components, and generate comprehensive documentation."
            ),
            tools=[
                self.read_vue_file,
                self.analyze_vue_component,
                self.identify_dependencies,
                self.generate_documentation,
            ],
            model="gpt-4o",
        )
    
    @function_tool
    def read_vue_file(self, file_path: str) -> str:
        """Read a Vue file from the specified path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    @function_tool
    def analyze_vue_component(self, file_path: str, content: str) -> VueComponent:
        """
        Analyze a Vue component and extract its structure.
        
        Args:
            file_path: Path to the Vue component file
            content: Content of the Vue component file
            
        Returns:
            A VueComponent object with the extracted structure
        """
        template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        template = template_match.group(1).strip() if template_match else ""
        
        script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
        script = script_match.group(1).strip() if script_match else ""
        
        style_match = re.search(r'<style.*?>(.*?)</style>', content, re.DOTALL)
        style = style_match.group(1).strip() if style_match else None
        
        name_match = re.search(r'name:\s*[\'"](.+?)[\'"]', script)
        name = name_match.group(1) if name_match else os.path.basename(file_path).split('.')[0]
        
        props = self._extract_props(script)
        
        data = self._extract_data(script)
        
        computed = self._extract_computed(script)
        
        methods = self._extract_methods(script)
        
        lifecycle_hooks = self._extract_lifecycle_hooks(script)
        
        return VueComponent(
            name=name,
            template=template,
            script=script,
            style=style,
            props=props,
            data=data,
            computed=computed,
            methods=methods,
            lifecycle_hooks=lifecycle_hooks,
            dependencies=[],  # Will be filled by identify_dependencies
            file_path=file_path
        )
    
    def _extract_props(self, script: str) -> Dict[str, Dict]:
        """Extract props from the script section."""
        props = {}
        props_match = re.search(r'props:\s*{(.*?)}', script, re.DOTALL)
        
        if props_match:
            props_str = props_match.group(1)
            prop_entries = re.finditer(r'(\w+):\s*({.*?}|[^,}]+)', props_str, re.DOTALL)
            
            for entry in prop_entries:
                prop_name = entry.group(1)
                prop_def = entry.group(2).strip()
                
                if prop_def.startswith('{'):
                    type_match = re.search(r'type:\s*(\w+)', prop_def)
                    default_match = re.search(r'default:\s*([^,}]+)', prop_def)
                    required_match = re.search(r'required:\s*(true|false)', prop_def)
                    
                    prop_info = {}
                    if type_match:
                        prop_info['type'] = type_match.group(1)
                    if default_match:
                        prop_info['default'] = default_match.group(1).strip()
                    if required_match:
                        prop_info['required'] = required_match.group(1) == 'true'
                    
                    props[prop_name] = prop_info
                else:
                    props[prop_name] = {'type': prop_def}
        
        return props
    
    def _extract_data(self, script: str) -> Dict[str, any]:
        """Extract data properties from the script section."""
        data = {}
        data_match = re.search(r'data\s*\(\s*\)\s*{\s*return\s*{(.*?)}', script, re.DOTALL)
        
        if data_match:
            data_str = data_match.group(1)
            data_entries = re.finditer(r'(\w+):\s*([^,]+)', data_str)
            
            for entry in data_entries:
                data_name = entry.group(1)
                data_value = entry.group(2).strip()
                data[data_name] = data_value
        
        return data
    
    def _extract_computed(self, script: str) -> Dict[str, str]:
        """Extract computed properties from the script section."""
        computed = {}
        computed_match = re.search(r'computed:\s*{(.*?)}', script, re.DOTALL)
        
        if computed_match:
            computed_str = computed_match.group(1)
            computed_entries = re.finditer(r'(\w+)\s*\(\s*\)\s*{(.*?)}', computed_str, re.DOTALL)
            
            for entry in computed_entries:
                computed_name = entry.group(1)
                computed_impl = entry.group(2).strip()
                computed[computed_name] = computed_impl
        
        return computed
    
    def _extract_methods(self, script: str) -> Dict[str, str]:
        """Extract methods from the script section."""
        methods = {}
        methods_match = re.search(r'methods:\s*{(.*?)}', script, re.DOTALL)
        
        if methods_match:
            methods_str = methods_match.group(1)
            method_entries = re.finditer(r'(\w+)\s*\([^)]*\)\s*{(.*?)}', methods_str, re.DOTALL)
            
            for entry in method_entries:
                method_name = entry.group(1)
                method_impl = entry.group(2).strip()
                methods[method_name] = method_impl
        
        return methods
    
    def _extract_lifecycle_hooks(self, script: str) -> Dict[str, str]:
        """Extract lifecycle hooks from the script section."""
        lifecycle_hooks = {}
        hook_names = [
            'beforeCreate', 'created', 'beforeMount', 'mounted',
            'beforeUpdate', 'updated', 'beforeDestroy', 'destroyed',
            'activated', 'deactivated'
        ]
        
        for hook in hook_names:
            hook_match = re.search(rf'{hook}\s*\(\s*\)\s*{{(.*?)}}', script, re.DOTALL)
            if hook_match:
                lifecycle_hooks[hook] = hook_match.group(1).strip()
        
        return lifecycle_hooks
    
    @function_tool
    def identify_dependencies(self, components: List[VueComponent]) -> Dict[str, List[str]]:
        """
        Identify dependencies between Vue components.
        
        Args:
            components: List of Vue components to analyze
            
        Returns:
            A dictionary mapping component file paths to lists of dependency file paths
        """
        dependency_graph = {}
        component_map = {comp.name: comp for comp in components}
        
        for component in components:
            dependencies = []
            
            import_matches = re.finditer(r'import\s+(\w+)\s+from\s+[\'"](.+?)[\'"]', component.script)
            for match in import_matches:
                imported_name = match.group(1)
                imported_path = match.group(2)
                
                if imported_name in component_map:
                    dependencies.append(component_map[imported_name].file_path)
            
            for comp_name in component_map:
                if comp_name != component.name:
                    kebab_case = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', comp_name).lower()
                    if re.search(rf'<{kebab_case}[>\s]', component.template):
                        dependencies.append(component_map[comp_name].file_path)
                    
                    if re.search(rf'<{comp_name}[>\s]', component.template):
                        dependencies.append(component_map[comp_name].file_path)
            
            dependency_graph[component.file_path] = list(set(dependencies))  # Remove duplicates
        
        return dependency_graph
    
    @function_tool
    def generate_documentation(self, component: VueComponent) -> str:
        """
        Generate comprehensive documentation for a Vue component.
        
        Args:
            component: The Vue component to document
            
        Returns:
            Markdown documentation for the component
        """
        doc = f"# {component.name}\n\n"
        
        doc += "## Overview\n\n"
        doc += f"Vue component defined in `{component.file_path}`.\n\n"
        
        if component.props:
            doc += "## Props\n\n"
            doc += "| Name | Type | Required | Default | Description |\n"
            doc += "|------|------|----------|---------|-------------|\n"
            
            for name, prop in component.props.items():
                prop_type = prop.get('type', 'Any')
                required = prop.get('required', False)
                default_value = prop.get('default', '-')
                doc += f"| {name} | {prop_type} | {required} | {default_value} | - |\n"
            
            doc += "\n"
        
        if component.data:
            doc += "## Data Properties\n\n"
            doc += "| Name | Initial Value |\n"
            doc += "|------|---------------|\n"
            
            for name, value in component.data.items():
                doc += f"| {name} | {value} |\n"
            
            doc += "\n"
        
        if component.computed:
            doc += "## Computed Properties\n\n"
            for name, impl in component.computed.items():
                doc += f"### {name}\n\n"
                doc += "```javascript\n"
                doc += impl + "\n"
                doc += "```\n\n"
        
        if component.methods:
            doc += "## Methods\n\n"
            for name, impl in component.methods.items():
                doc += f"### {name}\n\n"
                doc += "```javascript\n"
                doc += impl + "\n"
                doc += "```\n\n"
        
        if component.lifecycle_hooks:
            doc += "## Lifecycle Hooks\n\n"
            for hook, impl in component.lifecycle_hooks.items():
                doc += f"### {hook}\n\n"
                doc += "```javascript\n"
                doc += impl + "\n"
                doc += "```\n\n"
        
        doc += "## Control Flow Analysis\n\n"
        
        conditionals = re.findall(r'v-if="([^"]+)"', component.template)
        if conditionals:
            doc += "### Conditional Rendering\n\n"
            for cond in conditionals:
                doc += f"- `v-if=\"{cond}\"`\n"
            doc += "\n"
        
        lists = re.findall(r'v-for="([^"]+)"', component.template)
        if lists:
            doc += "### List Rendering\n\n"
            for lst in lists:
                doc += f"- `v-for=\"{lst}\"`\n"
            doc += "\n"
        
        events = re.findall(r'@(\w+)="([^"]+)"', component.template)
        if events:
            doc += "### Event Handling\n\n"
            for event, handler in events:
                doc += f"- `@{event}=\"{handler}\"`\n"
            doc += "\n"
        
        if component.dependencies:
            doc += "## Dependencies\n\n"
            for dep in component.dependencies:
                doc += f"- `{dep}`\n"
            doc += "\n"
        
        return doc
    
    async def analyze_directory(self, directory_path: str) -> FileAnalysisResult:
        """
        Analyze all Vue files in a directory.
        
        Args:
            directory_path: Path to the directory containing Vue files
            
        Returns:
            A FileAnalysisResult object with the analysis results
        """
        from agents import Runner
        
        vue_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.vue'):
                    vue_files.append(os.path.join(root, file))
        
        components = []
        for file_path in vue_files:
            result = await Runner.run(
                self.agent,
                f"Analyze the Vue component at {file_path}",
            )
            component = result.final_output_as(VueComponent)
            components.append(component)
        
        dependency_graph = await Runner.run(
            self.agent,
            f"Identify dependencies between the {len(components)} components",
        )
        dependency_graph = dependency_graph.final_output_as(Dict[str, List[str]])
        
        for component in components:
            component.dependencies = dependency_graph.get(component.file_path, [])
        
        documentation = {}
        for component in components:
            result = await Runner.run(
                self.agent,
                f"Generate documentation for the component {component.name}",
            )
            documentation[component.file_path] = result.final_output
        
        return FileAnalysisResult(
            components=components,
            dependency_graph=dependency_graph,
            documentation=documentation
        )
