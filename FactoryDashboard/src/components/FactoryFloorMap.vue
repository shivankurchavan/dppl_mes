<template>
  <v-stage :config="stageSize">
    <v-layer>
      <v-image
        v-if="backgroundImage"
        :config="floorPlanConfig"
      />
    </v-layer>
    <v-layer>
      <v-line
        v-for="(area, key) in areas"
        :key="key"
        :config="{
          points: area.points,
          fill: area.color,
          opacity: hoveredArea === key ? 0.5 : 0,
          closed: true
        }"
        @mouseover="handleMouseOver(key)"
        @mouseout="handleMouseOut"
        @mousemove="(e) => handleMouseMove(e, key)"
      />
    </v-layer>
    <v-layer>
      <v-label
        :config="{
          x: tooltipProps.x,
          y: tooltipProps.y,
          opacity: 0.75,
          visible: tooltipProps.visible
        }"
      >
        <v-tag
          :config="{
            fill: 'black',
            pointerDirection: 'down',
            pointerWidth: 10,
            pointerHeight: 10,
            lineJoin: 'round',
            shadowColor: 'black',
            shadowBlur: 10,
            shadowOffsetX: 10,
            shadowOffsetY: 10,
            shadowOpacity: 0.5
          }"
        />
        <v-text
          :config="{
            text: tooltipProps.text,
            fontFamily: 'Calibri',
            fontSize: 18,
            padding: 5,
            fill: 'white'
          }"
        />
      </v-label>
    </v-layer>
  </v-stage>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useImage } from 'vue-konva';

const stageSize = {
  width: window.innerWidth,
  height: window.innerHeight
};

const [backgroundImage] = useImage('./src/assets/floor-plan.svg');


// Reactive object to store image dimensions
const imageDimensions = ref({
  width: 0,
  height: 0
});

// Watch for changes to backgroundImage to update dimensions
// watch(
//   () => backgroundImage.value,
//   (newImage) => {
//     if (newImage && newImage.complete) {
//       // Image is already loaded
//       imageDimensions.value = {
//         width: newImage.naturalWidth,
//         height: newImage.naturalHeight
//       };
//       console.log('Image loaded - Natural Width:', newImage.naturalWidth);
//       console.log('Image loaded - Natural Height:', newImage.naturalHeight);
//     } else if (newImage) {
//       // Image exists but not yet loaded
//       newImage.onload = () => {
//         imageDimensions.value = {
//           width: newImage.naturalWidth,
//           height: newImage.naturalHeight
//         };
//         console.log('Image loaded (onload) - Natural Width:', newImage.naturalWidth);
//         console.log('Image loaded (onload) - Natural Height:', newImage.naturalHeight);
//       };
//       newImage.onerror = () => {
//         console.error('Failed to load image at ./src/assets/floor-plan.svg');
//       };
//     } else {
//       console.warn('backgroundImage is null or undefined');
//     }
//   },
//   { immediate: true } // Run immediately to check initial state
// );

const getData = () => ({
  '1st Floor': {
    color: 'blue',
    points: [366, 298, 500, 284, 499, 204, 352, 183, 72, 228, 74, 274],
  },
  '2nd Floor': {
    color: 'red',
    points: [72, 228, 73, 193, 340, 96, 498, 154, 498, 191, 341, 171],
  },
  '3rd Floor': {
    color: 'yellow',
    points: [73, 192, 73, 160, 340, 23, 500, 109, 499, 139, 342, 93, 100, 200, 400, 500, 600, 700],
  },
  Gym: {
    color: 'green',
    points: [498, 283, 503, 146, 560, 136, 576, 144, 576, 278, 500, 283],
  },
});

// Optional: Computed property for scaling the image (uncomment and adapt if needed)
const floorPlanConfig = computed(() => {
  if (!backgroundImage.value) return {};

  const imageWidth = backgroundImage.value.naturalWidth;
  const imageHeight = backgroundImage.value.naturalHeight;
  const stageWidth = stageSize.width;
  const stageHeight = stageSize.height;

  // Calculate scale factor to fit rotated image into stage
  const scaleX = stageWidth / imageHeight;
  const scaleY = stageHeight / imageWidth;
  const scale = Math.min(scaleX, scaleY);

  const scaledWidth = imageWidth * scale;
  const scaledHeight = imageHeight * scale;

  return {
    image: backgroundImage.value,
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

const areas = getData();
const hoveredArea = ref(null);
const tooltipProps = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
});

const handleMouseOver = (key) => {
  hoveredArea.value = key;
};

const handleMouseOut = () => {
  hoveredArea.value = null;
  tooltipProps.value.visible = false;
};

const handleMouseMove = (e, key) => {
  const stage = e.target.getStage();
  const mousePos = stage.getPointerPosition();
  tooltipProps.value = {
    visible: true,
    x: mousePos.x,
    y: mousePos.y - 5,
    text: key,
  };
};
</script>
