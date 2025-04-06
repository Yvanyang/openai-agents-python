"""Code conversion agent for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os
import re

from agents import Agent, function_tool
from pydantic import BaseModel

from ..models import VueComponent, ReactComponent, KnowledgeBase, ConversionIssue


class CodeConversionAgent:
    """Agent for converting Vue components to React components."""
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        """
        Initialize the code conversion agent.
        
        Args:
            knowledge_base: Optional knowledge base for conversion rules
        """
        self.knowledge_base = knowledge_base
        self.agent = Agent(
            name="CodeConversionAgent",
            instructions=(
                "You are a specialized agent for converting Vue.js components to React components. "
                "Your task is to analyze Vue components and convert them to equivalent React components "
                "following best practices and maintaining the same functionality."
            ),
            tools=[
                self.convert_template_to_jsx,
                self.convert_script_to_react,
                self.convert_style_to_css,
                self.apply_knowledge_base_rules,
                self.create_react_component,
                self.write_react_component,
            ],
            model="gpt-4o",
        )
    
    @function_tool
    def convert_template_to_jsx(self, component: VueComponent) -> str:
        """
        Convert Vue template to React JSX.
        
        Args:
            component: The Vue component to convert
            
        Returns:
            JSX code for the React component
        """
        template = component.template
        
        
        template = re.sub(
            r'<([a-zA-Z0-9_-]+)([^>]*?)v-if="([^"]+)"([^>]*?)>',
            r'{\3 && <\1\2\4>}',
            template
        )
        
        def replace_v_for(match):
            tag = match.group(1)
            attrs = match.group(2)
            v_for_expr = match.group(3)
            rest_attrs = match.group(4)
            
            if " in " in v_for_expr:
                item, collection = v_for_expr.split(" in ")
                item = item.strip()
                collection = collection.strip()
                
                if "," in item:
                    item_parts = item.strip("()").split(",")
                    item = item_parts[0].strip()
                    index = item_parts[1].strip()
                    return f"{{{collection}.map(({item}, {index}) => <{tag}{attrs}{rest_attrs}>)}}"
                else:
                    return f"{{{collection}.map(({item}, index) => <{tag}{attrs}{rest_attrs} key={{index}}>)}}"
            else:
                return match.group(0)
        
        template = re.sub(
            r'<([a-zA-Z0-9_-]+)([^>]*?)v-for="([^"]+)"([^>]*?)>',
            replace_v_for,
            template
        )
        
        template = re.sub(
            r'<input([^>]*?)v-model="([^"]+)"([^>]*?)>',
            r'<input\1value={\2} onChange={(e) => set\2(e.target.value)}\3>',
            template
        )
        
        template = re.sub(
            r'(v-bind:|:)([a-zA-Z0-9_-]+)="([^"]+)"',
            r'\2={\3}',
            template
        )
        
        def replace_event(match):
            event = match.group(1)
            handler = match.group(2)
            
            event_capitalized = event[0].upper() + event[1:]
            
            if "(" in handler and ")" in handler:
                method_name = handler.split("(")[0]
                params = handler.split("(")[1].split(")")[0]
                return f"on{event_capitalized}={{(e) => {method_name}({params})}}"
            else:
                return f"on{event_capitalized}={{{handler}}}"
        
        template = re.sub(
            r'(v-on:|@)([a-zA-Z0-9_-]+)="([^"]+)"',
            replace_event,
            template
        )
        
        def replace_component_tag(match):
            tag = match.group(1)
            attrs = match.group(2)
            
            if "-" in tag:
                parts = tag.split("-")
                pascal_case = "".join(part.capitalize() for part in parts)
                return f"<{pascal_case}{attrs}"
            else:
                return match.group(0)
        
        template = re.sub(
            r'<([a-z0-9-]+)([^>]*?)(?=>)',
            replace_component_tag,
            template
        )
        
        def replace_closing_tag(match):
            tag = match.group(1)
            
            if "-" in tag:
                parts = tag.split("-")
                pascal_case = "".join(part.capitalize() for part in parts)
                return f"</{pascal_case}>"
            else:
                return match.group(0)
        
        template = re.sub(
            r'</([a-z0-9-]+)>',
            replace_closing_tag,
            template
        )
        
        template = re.sub(
            r'class="([^"]+)"',
            r'className="\1"',
            template
        )
        
        if self.knowledge_base:
            for rule in self.knowledge_base.rules:
                template = re.sub(rule.pattern, rule.replacement, template)
        
        return template
    
    @function_tool
    def convert_script_to_react(self, component: VueComponent) -> Dict:
        """
        Convert Vue script to React hooks and functions.
        
        Args:
            component: The Vue component to convert
            
        Returns:
            A dictionary containing React imports, props, state, effects, and methods
        """
        imports = [
            "import React, { useState, useEffect } from 'react';",
        ]
        
        props = component.props
        
        state = {}
        for name, value in component.data.items():
            state[name] = value
        
        computed = []
        for name, impl in component.computed.items():
            deps = re.findall(r'this\.([a-zA-Z0-9_]+)', impl)
            deps = [dep for dep in deps if dep in state or dep in props]
            
            computed.append({
                "name": name,
                "implementation": impl,
                "dependencies": deps
            })
            
            if "useMemo" not in imports[0]:
                imports[0] = imports[0].replace("}", ", useMemo }")
        
        methods = {}
        for name, impl in component.methods.items():
            impl = re.sub(r'this\.([a-zA-Z0-9_]+)', r'\1', impl)
            methods[name] = impl
        
        effects = []
        lifecycle_mapping = {
            "created": "[]",  # Run once on mount
            "mounted": "[]",  # Run once on mount
            "updated": None,  # Run on every update
            "beforeDestroy": None,  # Return a cleanup function
            "destroyed": None,  # Return a cleanup function
        }
        
        if self.knowledge_base and hasattr(self.knowledge_base, "lifecycle_mappings"):
            lifecycle_mapping.update(self.knowledge_base.lifecycle_mappings)
        
        for hook, impl in component.lifecycle_hooks.items():
            if hook in lifecycle_mapping:
                deps = lifecycle_mapping[hook]
                
                impl = re.sub(r'this\.([a-zA-Z0-9_]+)', r'\1', impl)
                
                if hook in ["beforeDestroy", "destroyed"]:
                    effects.append({
                        "implementation": f"() => {{\n{impl}\n}}",
                        "dependencies": "[]"
                    })
                else:
                    effects.append({
                        "implementation": impl,
                        "dependencies": deps
                    })
        
        return {
            "imports": imports,
            "props": props,
            "state": state,
            "computed": computed,
            "methods": methods,
            "effects": effects
        }
    
    @function_tool
    def convert_style_to_css(self, component: VueComponent) -> Optional[str]:
        """
        Convert Vue style to CSS.
        
        Args:
            component: The Vue component to convert
            
        Returns:
            CSS code for the React component, or None if no style is present
        """
        if not component.style:
            return None
        
        style = component.style
        
        if "<style scoped>" in component.script:
            component_class = f"{component.name.lower()}-component"
            style = re.sub(
                r'^([a-zA-Z0-9_.-]+\s*{)',
                f'.{component_class} \\1',
                style,
                flags=re.MULTILINE
            )
        
        return style
    
    @function_tool
    def apply_knowledge_base_rules(
        self, jsx: str, react_script: Dict, css: Optional[str]
    ) -> Dict:
        """
        Apply knowledge base rules to the converted code.
        
        Args:
            jsx: JSX code for the React component
            react_script: Dictionary containing React hooks and functions
            css: CSS code for the React component
            
        Returns:
            Updated dictionary with converted code
        """
        if not self.knowledge_base:
            return {
                "jsx": jsx,
                "react_script": react_script,
                "css": css
            }
        
        for rule in self.knowledge_base.rules:
            jsx = re.sub(rule.pattern, rule.replacement, jsx)
        
        if hasattr(self.knowledge_base, "special_cases"):
            for case_name, case_data in self.knowledge_base.special_cases.items():
                if "pattern" in case_data and "replacement" in case_data:
                    jsx = re.sub(case_data["pattern"], case_data["replacement"], jsx)
        
        return {
            "jsx": jsx,
            "react_script": react_script,
            "css": css
        }
    
    @function_tool
    def create_react_component(
        self, component_name: str, jsx: str, react_script: Dict, css: Optional[str]
    ) -> ReactComponent:
        """
        Create a React component from the converted code.
        
        Args:
            component_name: Name of the React component
            jsx: JSX code for the React component
            react_script: Dictionary containing React hooks and functions
            css: CSS code for the React component
            
        Returns:
            A ReactComponent object
        """
        imports = react_script["imports"]
        props = react_script["props"]
        state = react_script["state"]
        computed = react_script["computed"]
        methods = react_script["methods"]
        effects = react_script["effects"]
        
        component_code = "\n".join(imports) + "\n\n"
        
        if props:
            component_code += "import PropTypes from 'prop-types';\n\n"
        
        component_code += f"function {component_name}("
        
        if props:
            prop_names = list(props.keys())
            component_code += "{ " + ", ".join(prop_names) + " }"
        
        component_code += ") {\n"
        
        for name, value in state.items():
            component_code += f"  const [{name}, set{name[0].upper()}{name[1:]}] = useState({value});\n"
        
        for comp in computed:
            deps_str = ", ".join(comp["dependencies"])
            component_code += f"  const {comp['name']} = useMemo(() => {{\n"
            component_code += f"    {comp['implementation']}\n"
            component_code += f"  }}, [{deps_str}]);\n"
        
        for name, impl in methods.items():
            component_code += f"  const {name} = () => {{\n"
            component_code += f"    {impl}\n"
            component_code += "  };\n"
        
        for effect in effects:
            component_code += f"  useEffect(() => {{\n"
            component_code += f"    {effect['implementation']}\n"
            component_code += f"  }}, {effect['dependencies']});\n"
        
        component_code += "\n  return (\n"
        component_code += f"    {jsx}\n"
        component_code += "  );\n"
        component_code += "}\n\n"
        
        if props:
            component_code += f"{component_name}.propTypes = {{\n"
            for name, prop in props.items():
                prop_type = prop.get("type", "Any")
                required = prop.get("required", False)
                
                prop_type_map = {
                    "String": "PropTypes.string",
                    "Number": "PropTypes.number",
                    "Boolean": "PropTypes.bool",
                    "Array": "PropTypes.array",
                    "Object": "PropTypes.object",
                    "Function": "PropTypes.func",
                }
                
                react_prop_type = prop_type_map.get(prop_type, "PropTypes.any")
                
                if required:
                    react_prop_type += ".isRequired"
                
                component_code += f"  {name}: {react_prop_type},\n"
            
            component_code += "};\n\n"
        
        component_code += f"export default {component_name};\n"
        
        return ReactComponent(
            name=component_name,
            imports=imports,
            props=props,
            state=state,
            effects=effects,
            methods=methods,
            jsx=jsx,
            css=css,
            file_path=""  # Will be set when writing the component
        )
    
    @function_tool
    def write_react_component(
        self, component: ReactComponent, output_dir: str
    ) -> str:
        """
        Write a React component to a file.
        
        Args:
            component: The React component to write
            output_dir: Directory to write the component to
            
        Returns:
            Path to the written file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        file_name = f"{component.name}.jsx"
        file_path = os.path.join(output_dir, file_name)
        
        imports = "\n".join(component.imports)
        
        if component.props:
            imports += "\nimport PropTypes from 'prop-types';"
        
        component_code = f"\n\nfunction {component.name}("
        
        if component.props:
            prop_names = list(component.props.keys())
            component_code += "{ " + ", ".join(prop_names) + " }"
        
        component_code += ") {\n"
        
        for name, value in component.state.items():
            component_code += f"  const [{name}, set{name[0].upper()}{name[1:]}] = useState({value});\n"
        
        for effect in component.effects:
            component_code += f"  useEffect(() => {{\n"
            component_code += f"    {effect['implementation']}\n"
            component_code += f"  }}, {effect['dependencies']});\n"
        
        for name, impl in component.methods.items():
            component_code += f"  const {name} = () => {{\n"
            component_code += f"    {impl}\n"
            component_code += "  };\n"
        
        component_code += "\n  return (\n"
        component_code += f"    {component.jsx}\n"
        component_code += "  );\n"
        component_code += "}\n\n"
        
        if component.props:
            component_code += f"{component.name}.propTypes = {{\n"
            for name, prop in component.props.items():
                prop_type = prop.get("type", "Any")
                required = prop.get("required", False)
                
                prop_type_map = {
                    "String": "PropTypes.string",
                    "Number": "PropTypes.number",
                    "Boolean": "PropTypes.bool",
                    "Array": "PropTypes.array",
                    "Object": "PropTypes.object",
                    "Function": "PropTypes.func",
                }
                
                react_prop_type = prop_type_map.get(prop_type, "PropTypes.any")
                
                if required:
                    react_prop_type += ".isRequired"
                
                component_code += f"  {name}: {react_prop_type},\n"
            
            component_code += "};\n\n"
        
        component_code += f"export default {component.name};\n"
        
        if component.css:
            css_file_name = f"{component.name}.css"
            css_file_path = os.path.join(output_dir, css_file_name)
            
            with open(css_file_path, 'w', encoding='utf-8') as css_file:
                css_file.write(component.css)
            
            imports = f"import './{css_file_name}';\n" + imports
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(imports + component_code)
        
        component.file_path = file_path
        
        return file_path
    
    async def convert_component(
        self, component: VueComponent, output_dir: str
    ) -> ReactComponent:
        """
        Convert a Vue component to a React component.
        
        Args:
            component: The Vue component to convert
            output_dir: Directory to write the converted component to
            
        Returns:
            The converted React component
        """
        from agents import Runner
        
        result = await Runner.run(
            self.agent,
            f"Convert the template of component {component.name} to JSX",
        )
        jsx = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Convert the script of component {component.name} to React hooks and functions",
        )
        react_script = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Convert the style of component {component.name} to CSS",
        )
        css = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Apply knowledge base rules to the converted code for component {component.name}",
        )
        converted_code = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Create a React component for {component.name}",
        )
        react_component = result.final_output_as(ReactComponent)
        
        result = await Runner.run(
            self.agent,
            f"Write the React component {react_component.name} to {output_dir}",
        )
        file_path = result.final_output
        
        react_component.file_path = file_path
        
        return react_component
    
    async def convert_batch(
        self, components: List[VueComponent], output_dir: str
    ) -> List[ReactComponent]:
        """
        Convert a batch of Vue components to React components.
        
        Args:
            components: The Vue components to convert
            output_dir: Directory to write the converted components to
            
        Returns:
            The converted React components
        """
        react_components = []
        
        for component in components:
            react_component = await self.convert_component(component, output_dir)
            react_components.append(react_component)
        
        return react_components
