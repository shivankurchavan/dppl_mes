<template>
  <div class="factory-dashboard">
    <div class="canvas-container">
      <v-stage
        ref="stage"
        :config="stageConfig"
        @wheel="handleWheel"
      >
        <!-- SVG Floor Plan Background Layer -->
        <v-layer ref="backgroundLayer">
          <v-image
            v-if="floorPlanImage"
            :config="floorPlanConfig"
          />
          <!-- Optional overlay for better visibility -->
          <v-rect
            :config="overlayConfig"
          />
        </v-layer>
      </v-stage>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFloorPlan } from '../composables/useFloorplan.js'

// Stage configuration with zoom and pan
const stageConfig = ref({
  width: window.innerWidth,
  height: window.innerHeight,
  scaleX: 1,
  scaleY: 1,
  x: 0,
  y: 0,
  draggable: true
})

// Floor plan configuration
const { floorPlanImage, loadFloorPlanAsModule } = useFloorPlan()

const floorPlanConfig = computed(() => {
  if (!floorPlanImage.value) return {};

  const imageWidth = floorPlanImage.value.naturalWidth;
  const imageHeight = floorPlanImage.value.naturalHeight;

  const stageWidth = stageConfig.value.width;
  const stageHeight = stageConfig.value.height;

  // Calculate scale factor to fit rotated image into stage
  const scaleX = stageWidth / imageHeight;
  const scaleY = stageHeight / imageWidth;
  const scale = Math.min(scaleX, scaleY);

  const scaledWidth = imageWidth * scale;
  const scaledHeight = imageHeight * scale;

  return {
    image: floorPlanImage.value,
    x: stageWidth / 2,
    y: stageHeight / 2,
    width: scaledWidth,
    height: scaledHeight,
    offsetX: scaledWidth / 2,
    offsetY: scaledHeight / 2,
    rotation: -90,
    opacity: 0.8,
  };
});

// Semi-transparent overlay for better machine visibility
const overlayConfig = computed(() => {
    if (!floorPlanConfig.value.width) return {};
    return {
        x: floorPlanConfig.value.x,
        y: floorPlanConfig.value.y,
        width: floorPlanConfig.value.width,
        height: floorPlanConfig.value.height,
        offsetX: floorPlanConfig.value.offsetX,
        offsetY: floorPlanConfig.value.offsetY,
        rotation: floorPlanConfig.value.rotation,
        fill: 'rgba(255, 255, 255, 0.1)',
        listening: false,
    };
});

// Event handlers
const handleWheel = (e) => {
  e.evt.preventDefault()
  
  const scaleBy = 1.05
  const stage = e.target.getStage()
  const oldScale = stage.scaleX()
  const pointer = stage.getPointerPosition()
  
  const newScale = e.evt.deltaY > 0 ? oldScale * scaleBy : oldScale / scaleBy
  
  // Limit zoom
  if (newScale < 0.5 || newScale > 3) return
  
  const mousePointTo = {
    x: (pointer.x - stage.x()) / oldScale,
    y: (pointer.y - stage.y()) / oldScale
  }
  
  const newPos = {
    x: pointer.x - mousePointTo.x * newScale,
    y: pointer.y - mousePointTo.y * newScale
  }
  
  stageConfig.value.scaleX = newScale
  stageConfig.value.scaleY = newScale
  stageConfig.value.x = newPos.x
  stageConfig.value.y = newPos.y
}

// Initialize
onMounted(async () => {
  await loadFloorPlanAsModule() // Use the module loader
})
</script>

<style scoped>
.factory-dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8f9fa;
}

.canvas-container {
  flex: 1;
  overflow: auto;
  position: relative;
  cursor: grab;
}

.canvas-container:active {
  cursor: grabbing;
}
</style>
