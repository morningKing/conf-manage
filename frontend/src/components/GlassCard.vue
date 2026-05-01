<template>
  <div
    class="glass-card"
    :class="{
      'glass-card-dark': dark,
      'glass-card-hoverable': hoverable
    }"
  >
    <!-- Header Section -->
    <div v-if="title || $slots.extra" class="glass-card-header">
      <div class="glass-card-title">
        <slot name="title">{{ title }}</slot>
      </div>
      <div class="glass-card-extra">
        <slot name="extra"></slot>
      </div>
    </div>

    <!-- Body Section -->
    <div class="glass-card-body">
      <slot></slot>
    </div>

    <!-- Footer Section -->
    <div v-if="$slots.footer" class="glass-card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * GlassCard - Glass-style card component
 *
 * A flexible card component with glass morphism styling.
 * Supports dark variant and hoverable state.
 *
 * @example
 * <GlassCard title="Card Title" :hoverable="true">
 *   <template #extra>
 *     <button>Action</button>
 *   </template>
 *   Card content here
 *   <template #footer>
 *     <button>Cancel</button>
 *     <button>Confirm</button>
 *   </template>
 * </GlassCard>
 */

// Props
defineProps({
  title: {
    type: String,
    default: ''
  },
  dark: {
    type: Boolean,
    default: false
  },
  hoverable: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
/* Base Card Styles */
.glass-card {
  background: var(--bg-tertiary, #2a2a40);
  border: 1px solid var(--border-secondary, rgba(102, 126, 234, 0.4));
  border-radius: 12px;
  padding: 15px;
  transition: all 0.3s ease;
}

/* Hoverable Variant */
.glass-card-hoverable {
  cursor: pointer;
}

.glass-card-hoverable:hover {
  border-color: var(--border-main, rgba(102, 126, 234, 0.6));
  background: var(--bg-secondary, #252536);
}

/* Dark Variant */
.glass-card-dark {
  background: rgba(30, 30, 50, 0.95);
  border-color: var(--border-gradient, rgba(102, 126, 234, 0.5));
}

.glass-card-dark.glass-card-hoverable:hover {
  border-color: var(--border-main, rgba(102, 126, 234, 0.6));
  background: rgba(30, 30, 50, 1);
}

/* Header Section */
.glass-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-low, rgba(102, 126, 234, 0.2));
}

.glass-card-dark .glass-card-header {
  border-bottom-color: var(--border-low, rgba(102, 126, 234, 0.2));
}

/* Title */
.glass-card-title {
  color: var(--text-primary, #fff);
  font-size: 14px;
  font-weight: 500;
}

/* Extra Slot */
.glass-card-extra {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Body Section */
.glass-card-body {
  color: var(--text-secondary, rgba(255, 255, 255, 0.85));
}

/* Footer Section */
.glass-card-footer {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-low, rgba(102, 126, 234, 0.2));
}

.glass-card-dark .glass-card-footer {
  border-top-color: var(--border-low, rgba(102, 126, 234, 0.2));
}
</style>