"""Conversion planning agent for the Vue-to-React converter."""

from typing import Dict, List, Optional
import os

from agents import Agent, function_tool
from pydantic import BaseModel

from ..models import ConversionBatch, ConversionPlan, VueComponent


class ConversionPlanningAgent:
    """Agent for planning the conversion of Vue components to React."""
    
    def __init__(self):
        """Initialize the conversion planning agent."""
        self.agent = Agent(
            name="ConversionPlanningAgent",
            instructions=(
                "You are a specialized agent for planning the conversion of Vue.js components to React. "
                "Your task is to analyze component dependencies and create an optimal conversion plan "
                "that determines the order in which components should be converted."
            ),
            tools=[
                self.create_dependency_graph,
                self.sort_components_by_dependencies,
                self.create_conversion_batches,
                self.create_conversion_plan,
            ],
            model="gpt-4o",
        )
    
    @function_tool
    def create_dependency_graph(self, components: List[VueComponent]) -> Dict[str, List[str]]:
        """
        Create a dependency graph for the given components.
        
        Args:
            components: List of Vue components
            
        Returns:
            A dictionary mapping component file paths to lists of dependency file paths
        """
        dependency_graph = {}
        
        for component in components:
            dependency_graph[component.file_path] = component.dependencies
        
        return dependency_graph
    
    @function_tool
    def sort_components_by_dependencies(
        self, components: List[VueComponent], dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        Sort components based on their dependencies using topological sorting.
        
        Args:
            components: List of Vue components
            dependency_graph: Dependency graph mapping component file paths to dependency file paths
            
        Returns:
            A list of component file paths in the order they should be converted
        """
        component_indices = {comp.file_path: i for i, comp in enumerate(components)}
        
        graph = {i: [] for i in range(len(components))}
        for i, component in enumerate(components):
            for dep in dependency_graph.get(component.file_path, []):
                if dep in component_indices:
                    graph[component_indices[dep]].append(i)
        
        visited = [False] * len(components)
        temp = [False] * len(components)
        order = []
        
        def dfs(node):
            if temp[node]:
                return
            if visited[node]:
                return
            
            temp[node] = True
            
            for neighbor in graph[node]:
                dfs(neighbor)
            
            temp[node] = False
            visited[node] = True
            order.append(node)
        
        for i in range(len(components)):
            if not visited[i]:
                dfs(i)
        
        order.reverse()
        
        conversion_order = [components[i].file_path for i in order]
        return conversion_order
    
    @function_tool
    def create_conversion_batches(
        self, conversion_order: List[str], dependency_graph: Dict[str, List[str]], batch_size: int
    ) -> List[ConversionBatch]:
        """
        Create batches of components for conversion.
        
        Args:
            conversion_order: List of component file paths in the order they should be converted
            dependency_graph: Dependency graph mapping component file paths to dependency file paths
            batch_size: Maximum number of components in a batch
            
        Returns:
            A list of ConversionBatch objects
        """
        batches = []
        current_batch = []
        current_batch_deps = {}
        
        for file_path in conversion_order:
            if len(current_batch) >= batch_size:
                batches.append(
                    ConversionBatch(
                        files=current_batch.copy(),
                        dependencies=current_batch_deps.copy(),
                        priority=len(batches) + 1,
                    )
                )
                current_batch = []
                current_batch_deps = {}
            
            current_batch.append(file_path)
            current_batch_deps[file_path] = dependency_graph.get(file_path, [])
        
        if current_batch:
            batches.append(
                ConversionBatch(
                    files=current_batch,
                    dependencies=current_batch_deps,
                    priority=len(batches) + 1,
                )
            )
        
        return batches
    
    @function_tool
    def create_conversion_plan(
        self,
        batches: List[ConversionBatch],
        dependency_graph: Dict[str, List[str]],
        conversion_order: List[str],
    ) -> ConversionPlan:
        """
        Create a conversion plan for the given components.
        
        Args:
            batches: List of conversion batches
            dependency_graph: Dependency graph mapping component file paths to dependency file paths
            conversion_order: List of component file paths in the order they should be converted
            
        Returns:
            A ConversionPlan object
        """
        return ConversionPlan(
            batches=batches,
            dependency_graph=dependency_graph,
            conversion_order=conversion_order,
        )
    
    async def create_plan(
        self, components: List[VueComponent], batch_size: int = 5
    ) -> ConversionPlan:
        """
        Create a conversion plan for the given components.
        
        Args:
            components: List of Vue components to convert
            batch_size: Maximum number of components in a batch
            
        Returns:
            A ConversionPlan object
        """
        from agents import Runner
        
        result = await Runner.run(
            self.agent,
            f"Create a dependency graph for {len(components)} components",
        )
        dependency_graph = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Sort {len(components)} components by dependencies",
        )
        conversion_order = result.final_output
        
        result = await Runner.run(
            self.agent,
            f"Create conversion batches with batch size {batch_size}",
        )
        batches = result.final_output
        
        result = await Runner.run(
            self.agent,
            "Create a conversion plan",
        )
        conversion_plan = result.final_output_as(ConversionPlan)
        
        return conversion_plan
