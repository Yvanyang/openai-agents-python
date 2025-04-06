"""Tests for the Vue-to-React converter."""

import asyncio
import os
import shutil
import tempfile
import unittest

from src import VueToReactConverter


class TestVueToReactConverter(unittest.TestCase):
    """Test cases for the Vue-to-React converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.source_dir = tempfile.mkdtemp()
        self.destination_dir = tempfile.mkdtemp()
        
        self.vue_file_path = os.path.join(self.source_dir, "Counter.vue")
        with open(self.vue_file_path, "w", encoding="utf-8") as f:
            f.write("""
<template>
  <div class="counter-container">
    <h1>{{ title }}</h1>
    <p>Count: {{ count }}</p>
    <button @click="increment">Increment</button>
    <button @click="decrement">Decrement</button>
    <div v-if="count > 5" class="warning">
      Count is getting high!
    </div>
  </div>
</template>

<script>
export default {
  name: 'Counter',
  props: {
    title: {
      type: String,
      default: 'Counter Example'
    },
    initialCount: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      count: this.initialCount
    }
  },
  methods: {
    increment() {
      this.count += 1;
    },
    decrement() {
      this.count -= 1;
    }
  },
  mounted() {
    console.log('Counter component mounted');
  }
}
</script>

<style>
.counter-container {
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.warning {
  color: red;
  font-weight: bold;
}
</style>
""")
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.destination_dir)
    
    def test_converter_initialization(self):
        """Test converter initialization."""
        converter = VueToReactConverter(
            source_dir=self.source_dir,
            destination_dir=self.destination_dir,
        )
        
        self.assertEqual(converter.source_dir, self.source_dir)
        self.assertEqual(converter.destination_dir, self.destination_dir)
        self.assertEqual(converter.batch_size, 5)
        self.assertEqual(converter.max_fix_iterations, 3)
    
    def test_file_analysis(self):
        """Test file analysis."""
        converter = VueToReactConverter(
            source_dir=self.source_dir,
            destination_dir=self.destination_dir,
        )
        
        components = asyncio.run(converter.analyze_source_directory())
        
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].name, "Counter")
        self.assertEqual(components[0].file_path, self.vue_file_path)
        
        self.assertEqual(len(components[0].props), 2)
        self.assertIn("title", components[0].props)
        self.assertIn("initialCount", components[0].props)
        
        self.assertEqual(len(components[0].data), 1)
        self.assertIn("count", components[0].data)
        
        self.assertEqual(len(components[0].methods), 2)
        self.assertIn("increment", components[0].methods)
        self.assertIn("decrement", components[0].methods)
        
        self.assertEqual(len(components[0].lifecycle_hooks), 1)
        self.assertIn("mounted", components[0].lifecycle_hooks)
    
    def test_conversion_plan(self):
        """Test conversion plan creation."""
        converter = VueToReactConverter(
            source_dir=self.source_dir,
            destination_dir=self.destination_dir,
        )
        
        asyncio.run(converter.analyze_source_directory())
        
        plan = asyncio.run(converter.create_conversion_plan())
        
        self.assertEqual(len(plan.batches), 1)
        self.assertEqual(len(plan.conversion_order), 1)
        self.assertEqual(plan.conversion_order[0], self.vue_file_path)
    
    def test_full_conversion(self):
        """Test the full conversion process."""
        converter = VueToReactConverter(
            source_dir=self.source_dir,
            destination_dir=self.destination_dir,
        )
        
        report = asyncio.run(converter.run())
        
        self.assertEqual(report.total_files, 1)
        
        component_dir = os.path.join(self.destination_dir, "components", "Counter")
        self.assertTrue(os.path.exists(component_dir))
        
        react_file_path = os.path.join(component_dir, "Counter.jsx")
        self.assertTrue(os.path.exists(react_file_path))
        
        css_file_path = os.path.join(component_dir, "Counter.css")
        self.assertTrue(os.path.exists(css_file_path))
        
        docs_dir = os.path.join(self.destination_dir, "docs")
        self.assertTrue(os.path.exists(docs_dir))
        
        doc_file_path = os.path.join(docs_dir, "Counter.md")
        self.assertTrue(os.path.exists(doc_file_path))
        
        plan_file_path = os.path.join(docs_dir, "conversion_plan.md")
        self.assertTrue(os.path.exists(plan_file_path))
        
        report_file_path = os.path.join(docs_dir, "conversion_report.md")
        self.assertTrue(os.path.exists(report_file_path))


if __name__ == "__main__":
    unittest.main()
