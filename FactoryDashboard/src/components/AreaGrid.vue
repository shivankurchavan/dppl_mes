<template>
  <div class="area-grid">
    <h3>{{ areaName }}</h3>
    <div class="machine-cards-container">
      <MachineCard 
        v-for="machine in machines"
        :key="machine.id"
        :machine="machine"
        @card-clicked="handleCardClick"
      />
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import MachineCard from './MachineCard.vue';

const props = defineProps({
  areaName: String,
  machines: Array
});

const emit = defineEmits(['machine-card-clicked']);

const handleCardClick = (id) => {
  emit('machine-card-clicked', id);
};
</script>


<style scoped>
.area-grid {
  margin-bottom: 20px;
}

.area-grid h3 {
  margin-bottom: 10px;
  font-size: 18px;
  border-bottom: 1px solid #eeeeee;
  padding-bottom: 5px;
}

.machine-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}
</style>