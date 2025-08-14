<template>
  <div id="app">
    <header>
      <nav class="top-bar">
        <div class="navbar-left">
          <!-- Space for logo -->
          <div class="logo-placeholder"></div>
          <span class="navbar-title">Factory Dashboard</span>
        </div>
      </nav>
      <nav class="controls-bar">
        <button v-if="isMachineDetailsView" @click="goBackToDashboard">&larr; Back</button>
        <button v-else @click="toggleView">Switch to {{ isFloorMapView ? 'Dashboard' : 'Floor Map' }}</button>
        <div class="filters" :class="{ 'disabled': isFloorMapView || isMachineDetailsView }">
          <FilterDropdown 
            id="factory-filter"
            label="Factory"
            :options="factoryOptions"
            @filter-selected="handleFilterSelected('factory', $event)"
          />
          <FilterDropdown 
            id="area-filter"
            label="Area"
            :options="areaOptions"
            @filter-selected="handleFilterSelected('area', $event)"
          />
          <!-- <FilterDropdown 
            id="status-filter"
            label="Running Status"
            :options="statusOptions"
            @filter-selected="handleFilterSelected('status', $event)"
          /> -->
        </div>
      </nav>
    </header>
    <router-view class="view-content" v-slot="{ Component }">
      <component :is="Component" :selected-filters="selectedFilters" />
    </router-view>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router';
import { ref, watch } from 'vue';
import { createListResource } from 'frappe-ui';
import FilterDropdown from './components/FilterDropdown.vue';

const router = useRouter();
const route = useRoute();

const isFloorMapView = ref(false);
const isMachineDetailsView = ref(false);

watch(() => route.name, (newName) => {
  isFloorMapView.value = newName === 'FactoryFloorMap';
  isMachineDetailsView.value = newName === 'MachineDetails';
}, { immediate: true });

const toggleView = () => {
  if (route.name === 'FactoryFloorMap') {
    router.push({ name: 'Dashboard' });
  } else {
    router.push({ name: 'FactoryFloorMap' });
  }
};


const goBackToDashboard = () => {
  router.push({ name: 'Dashboard' });
};

// Fetch factory and area options
const factoryResource = createListResource({
  doctype: 'Factory',
  fields: ['factory_name'],
  orderBy: 'factory_name',
  auto: true,
});

const areaResource = createListResource({
  doctype: 'Area',
  fields: ['area_name'],
  orderBy: 'area_name',
  auto: true,
});

// console.log('Factory Resource:', factoryResource);
// console.log('Area Resource:', areaResource);

const factoryOptions = ref([]);
const areaOptions = ref([]);

// Map fetched data to filter options
watch(() => factoryResource.data, (data) => {
  if (data) {
    factoryOptions.value = data.map(f => ({ value: f.factory_name, text: f.factory_name }));
  }
}, { immediate: true });

watch(() => areaResource.data, (data) => {
  if (data) {
    areaOptions.value = data.map(a => ({ value: a.area_name, text: a.area_name }));
  }
}, { immediate: true });

const selectedFilters = ref({
  factory: '',
  area: '',
});

const handleFilterSelected = (filterName, value) => {
  selectedFilters.value[filterName] = value;
};
</script>


<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  display: flex;
  align-items: center;
  padding: 16px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: #f7f8fa;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(60, 72, 88, 0.08);
  border: 1px solid #e5e7eb;
  margin: 18px 32px 0 32px;
  position: relative;
  z-index: 10;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.logo-placeholder {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  border-radius: 8px;
  margin-right: 12px;
  box-shadow: 0 2px 8px rgba(100, 116, 139, 0.15);
  position: relative;
  overflow: hidden;
}

.logo-placeholder::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 16px;
  height: 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
}

.navbar-title {
  font-size: 20px;
  font-weight: 600;
  color: #334155;
  letter-spacing: 0.3px;
}

.controls-bar button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.25px;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  position: relative;
  overflow: hidden;
}

.controls-bar button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.4s;
}

.controls-bar button:hover::before {
  left: 100%;
}

.controls-bar button:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.controls-bar button:active {
  transform: translateY(0px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.filters {
  display: flex;
  gap: 3rem;
  align-items: center;
  padding-left: 8px;
  padding-right: 8px;
}

.filters :deep(label) {
  font-size: 3rem;
  font-weight: 900;
  color: #334155;
  margin-bottom: 4px;
  letter-spacing: 0.2px;
  display: block;
}

.filters.disabled {
  opacity: 0.5;
  pointer-events: none;
  filter: grayscale(50%);
  transition: all 0.2s ease;
}

.view-content {
  flex-grow: 1;
  overflow: auto;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}
</style>