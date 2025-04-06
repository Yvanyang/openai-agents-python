"""Knowledge base manager for the Vue-to-React converter."""

from typing import Dict, List, Optional
import json
import os

from agents import Agent, function_tool
from pydantic import BaseModel

from ..models import KnowledgeBase, KnowledgeBaseRule


class KnowledgeBaseManager:
    """Manager for the knowledge base used in Vue to React conversion."""
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize the knowledge base manager.
        
        Args:
            knowledge_base_path: Optional path to a JSON knowledge base file
        """
        self.knowledge_base = None
        self.agent = Agent(
            name="KnowledgeBaseManager",
            instructions=(
                "You are a specialized agent for managing knowledge bases for Vue to React conversion. "
                "Your task is to load, validate, and apply knowledge base rules during the conversion process."
            ),
            tools=[
                self.load_knowledge_base,
                self.validate_knowledge_base,
                self.create_default_knowledge_base,
                self.save_knowledge_base,
                self.get_rule_for_pattern,
            ],
            model="gpt-4o",
        )
        
        if knowledge_base_path:
            self.load_knowledge_base(knowledge_base_path)
    
    @function_tool
    def load_knowledge_base(self, file_path: str) -> KnowledgeBase:
        """
        Load a knowledge base from a JSON file.
        
        Args:
            file_path: Path to the knowledge base JSON file
            
        Returns:
            A KnowledgeBase object
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Knowledge base file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        rules = []
        for rule_data in data.get("rules", []):
            rules.append(
                KnowledgeBaseRule(
                    pattern=rule_data["pattern"],
                    replacement=rule_data["replacement"],
                    description=rule_data["description"],
                    examples=rule_data.get("examples", {}),
                )
            )
        
        self.knowledge_base = KnowledgeBase(
            rules=rules,
            lifecycle_mappings=data.get("lifecycle_mappings", {}),
            directive_mappings=data.get("directive_mappings", {}),
            special_cases=data.get("special_cases", {}),
        )
        
        return self.knowledge_base
    
    @function_tool
    def validate_knowledge_base(self, knowledge_base: KnowledgeBase) -> bool:
        """
        Validate a knowledge base.
        
        Args:
            knowledge_base: The knowledge base to validate
            
        Returns:
            True if the knowledge base is valid, False otherwise
        """
        for rule in knowledge_base.rules:
            try:
                import re
                re.compile(rule.pattern)
            except re.error:
                print(f"Invalid regex pattern in rule: {rule.pattern}")
                return False
        
        valid_vue_hooks = [
            "beforeCreate", "created", "beforeMount", "mounted",
            "beforeUpdate", "updated", "beforeDestroy", "destroyed",
            "activated", "deactivated"
        ]
        
        for vue_hook in knowledge_base.lifecycle_mappings:
            if vue_hook not in valid_vue_hooks:
                print(f"Invalid Vue lifecycle hook: {vue_hook}")
                return False
        
        valid_vue_directives = [
            "v-if", "v-else", "v-else-if", "v-for", "v-show",
            "v-bind", "v-on", "v-model", "v-text", "v-html",
            "v-pre", "v-cloak", "v-once"
        ]
        
        for vue_directive in knowledge_base.directive_mappings:
            if vue_directive not in valid_vue_directives and not vue_directive.startswith("v-"):
                print(f"Invalid Vue directive: {vue_directive}")
                return False
        
        return True
    
    @function_tool
    def create_default_knowledge_base(self) -> KnowledgeBase:
        """
        Create a default knowledge base with common Vue to React conversion rules.
        
        Returns:
            A KnowledgeBase object with default rules
        """
        rules = [
            KnowledgeBaseRule(
                pattern=r'<template>(.*?)</template>',
                replacement=r'\1',
                description="Remove template tags",
                examples={
                    "before": "<template><div>Hello</div></template>",
                    "after": "<div>Hello</div>",
                },
            ),
            KnowledgeBaseRule(
                pattern=r'v-if="([^"]+)"',
                replacement=r'{\1 && ',
                description="Convert v-if to conditional rendering",
                examples={
                    "before": '<div v-if="show">Content</div>',
                    "after": '{show && <div>Content</div>}',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'v-else',
                replacement=r'',
                description="Convert v-else to conditional rendering",
                examples={
                    "before": '<div v-if="show">Content</div><div v-else>Other</div>',
                    "after": '{show ? <div>Content</div> : <div>Other</div>}',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'v-for="([^"]+) in ([^"]+)"',
                replacement=r'{\2.map((\1) => ',
                description="Convert v-for to map",
                examples={
                    "before": '<div v-for="item in items">{{item}}</div>',
                    "after": '{items.map((item) => <div>{item}</div>)}',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'v-model="([^"]+)"',
                replacement=r'value={\1} onChange={(e) => set\1(e.target.value)}',
                description="Convert v-model to value and onChange",
                examples={
                    "before": '<input v-model="name">',
                    "after": '<input value={name} onChange={(e) => setName(e.target.value)}>',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'@([a-zA-Z0-9_-]+)="([^"]+)"',
                replacement=r'on\1={(e) => \2}',
                description="Convert @ event handlers to on[Event]",
                examples={
                    "before": '<button @click="handleClick">Click</button>',
                    "after": '<button onClick={(e) => handleClick}>Click</button>',
                },
            ),
            KnowledgeBaseRule(
                pattern=r':([a-zA-Z0-9_-]+)="([^"]+)"',
                replacement=r'\1={\2}',
                description="Convert : bindings to JSX attributes",
                examples={
                    "before": '<div :class="className">Content</div>',
                    "after": '<div className={className}>Content</div>',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'class="([^"]+)"',
                replacement=r'className="\1"',
                description="Convert class to className",
                examples={
                    "before": '<div class="container">Content</div>',
                    "after": '<div className="container">Content</div>',
                },
            ),
            KnowledgeBaseRule(
                pattern=r'{{ ([^}]+) }}',
                replacement=r'{\1}',
                description="Convert Vue interpolation to JSX",
                examples={
                    "before": '<div>{{ message }}</div>',
                    "after": '<div>{message}</div>',
                },
            ),
        ]
        
        lifecycle_mappings = {
            "beforeCreate": "[]",
            "created": "[]",
            "beforeMount": "[]",
            "mounted": "[]",
            "beforeUpdate": None,
            "updated": None,
            "beforeDestroy": "[]",
            "destroyed": "[]",
        }
        
        directive_mappings = {
            "v-if": "conditional rendering",
            "v-else": "conditional rendering",
            "v-else-if": "conditional rendering",
            "v-for": "map",
            "v-show": "style={{ display: condition ? '' : 'none' }}",
            "v-bind": "JSX attribute",
            "v-on": "on[Event]",
            "v-model": "value + onChange",
            "v-text": "children",
            "v-html": "dangerouslySetInnerHTML",
        }
        
        special_cases = {
            "computed_properties": {
                "pattern": r'computed:\s*{(.*?)}',
                "replacement": "useMemo",
                "description": "Convert computed properties to useMemo",
            },
            "watchers": {
                "pattern": r'watch:\s*{(.*?)}',
                "replacement": "useEffect",
                "description": "Convert watchers to useEffect",
            },
            "mixins": {
                "pattern": r'mixins:\s*\[(.*?)\]',
                "replacement": "custom hooks",
                "description": "Convert mixins to custom hooks",
            },
        }
        
        self.knowledge_base = KnowledgeBase(
            rules=rules,
            lifecycle_mappings=lifecycle_mappings,
            directive_mappings=directive_mappings,
            special_cases=special_cases,
        )
        
        return self.knowledge_base
    
    @function_tool
    def save_knowledge_base(self, file_path: str) -> bool:
        """
        Save the knowledge base to a JSON file.
        
        Args:
            file_path: Path to save the knowledge base to
            
        Returns:
            True if the knowledge base was saved successfully, False otherwise
        """
        if not self.knowledge_base:
            print("No knowledge base to save")
            return False
        
        data = {
            "rules": [
                {
                    "pattern": rule.pattern,
                    "replacement": rule.replacement,
                    "description": rule.description,
                    "examples": rule.examples,
                }
                for rule in self.knowledge_base.rules
            ],
            "lifecycle_mappings": self.knowledge_base.lifecycle_mappings,
            "directive_mappings": self.knowledge_base.directive_mappings,
            "special_cases": self.knowledge_base.special_cases,
        }
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
        
        return True
    
    @function_tool
    def get_rule_for_pattern(self, pattern: str) -> Optional[KnowledgeBaseRule]:
        """
        Get a rule for a specific pattern.
        
        Args:
            pattern: The pattern to look for
            
        Returns:
            A KnowledgeBaseRule object if found, None otherwise
        """
        if not self.knowledge_base:
            return None
        
        for rule in self.knowledge_base.rules:
            if rule.pattern == pattern:
                return rule
        
        return None
    
    async def initialize(self, knowledge_base_path: Optional[str] = None) -> KnowledgeBase:
        """
        Initialize the knowledge base.
        
        Args:
            knowledge_base_path: Optional path to a JSON knowledge base file
            
        Returns:
            A KnowledgeBase object
        """
        from agents import Runner
        
        if knowledge_base_path:
            result = await Runner.run(
                self.agent,
                f"Load the knowledge base from {knowledge_base_path}",
            )
            self.knowledge_base = result.final_output_as(KnowledgeBase)
        else:
            result = await Runner.run(
                self.agent,
                "Create a default knowledge base",
            )
            self.knowledge_base = result.final_output_as(KnowledgeBase)
        
        result = await Runner.run(
            self.agent,
            "Validate the knowledge base",
        )
        is_valid = result.final_output
        
        if not is_valid:
            raise ValueError("Invalid knowledge base")
        
        return self.knowledge_base
