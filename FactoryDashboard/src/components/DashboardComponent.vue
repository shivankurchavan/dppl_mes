<template>
  <div class="dashboard-container">
    <div v-if="filteredMachines.length > 0">
      <h2 class="factory-title">{{ factoryTitle }}</h2>
      <div class="area-grids-container">
        <AreaGrid 
          v-for="(machinesInArea, area) in groupedMachines"
          :key="area"
          :areaName="area"
          :machines="machinesInArea"
          @machine-card-clicked="handleMachineCardClick"
        />
      </div>
    </div>
    <div v-else-if="machineResource.loading" class="loading-message">
      Loading machines...
    </div>
    <div v-else class="no-data-message">
      No machines match the selected criteria.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { createListResource } from 'frappe-ui';
import AreaGrid from './AreaGrid.vue';

const props = defineProps({
  selectedFilters: {
    type: Object,
    required: true,
  },
});

const router = useRouter();
const machines = ref([]);

// Initialize createListResource for Machine DocType
const machineResource = createListResource({
  doctype: 'Machine',
  fields: ['machine_name', 'is_active', 'factory', 'area', 'oem_code'], // Updated fields
  orderBy: 'machine_name',
  auto: false,
  filters: {},
});

// Watch for filter changes and refetch data
watch(
  () => props.selectedFilters,
  (newFilters) => {
    const filters = {};
    if (newFilters.factory) filters.factory = newFilters.factory;
    if (newFilters.area) filters.area = newFilters.area;

    machineResource.reload({
      filters,
    }).catch((error) => {
      console.error('Error applying filters:', error);
    });
  },
  { deep: true, immediate: true }
);

// Map fetched data to the expected machine structure
watch(
  () => machineResource.data,
  (newData) => {
    if (newData) {
      machines.value = newData.map(machine => ({
        id: machine.machine_name, // Use machine_name as id
        name: machine.machine_name,
        status: machine.is_active ? 'running' : 'stopped',
        factory: machine.factory,
        area: machine.area,
        oem_code: machine.oem_code,
      }));
    }
  },
  { immediate: true }
);

const factoryTitle = computed(() => {
  return props.selectedFilters.factory ? `${props.selectedFilters.factory}` : 'All Factories';
});

const filteredMachines = computed(() => {
  return machines.value.filter(machine => {
    const factoryMatch = !props.selectedFilters.factory || machine.factory === props.selectedFilters.factory;
    const areaMatch = !props.selectedFilters.area || machine.area === props.selectedFilters.area;
    return factoryMatch && areaMatch;
  });
});

const groupedMachines = computed(() => {
  const groups = {};
  filteredMachines.value.forEach(machine => {
    if (!groups[machine.area]) {
      groups[machine.area] = [];
    }
    groups[machine.area].push(machine);
  });
  return groups;
});

const handleMachineCardClick = (machineId) => {
  router.push({ name: 'MachineDetails', params: { id: machineId } });
};
</script>

<style scoped>
/* Existing styles unchanged */
.dashboard-container {
  padding: 20px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.factory-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #333;
}

.no-data-message,
.loading-message {
  text-align: center;
  margin-top: 50px;
  font-size: 18px;
  color: #666;
}

.area-grids-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>