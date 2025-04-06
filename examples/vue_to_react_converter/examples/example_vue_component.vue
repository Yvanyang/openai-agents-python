<template>
  <div class="counter-container">
    <h1>{{ title }}</h1>
    <p>Count: {{ count }}</p>
    <button @click="increment">Increment</button>
    <button @click="decrement">Decrement</button>
    <div v-if="count > 5" class="warning">
      Count is getting high!
    </div>
    <ul>
      <li v-for="item in items" :key="item.id">
        {{ item.text }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Counter',
  props: {
    title: {
      type: String,
      default: 'Counter Example',
      required: true
    },
    initialCount: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      count: this.initialCount,
      items: [
        { id: 1, text: 'Item 1' },
        { id: 2, text: 'Item 2' },
        { id: 3, text: 'Item 3' }
      ]
    }
  },
  computed: {
    doubleCount() {
      return this.count * 2;
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
  created() {
    console.log('Counter component created');
  },
  mounted() {
    console.log('Counter component mounted');
  },
  beforeDestroy() {
    console.log('Counter component will be destroyed');
  }
}
</script>

<style>
.counter-container {
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
  max-width: 400px;
  margin: 0 auto;
}

.warning {
  color: red;
  font-weight: bold;
}
</style>
