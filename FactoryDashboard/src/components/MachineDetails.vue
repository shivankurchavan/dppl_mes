<template>
  <div class="machine-details-container">
    <h2 class="page-title">Machine Details</h2>

    <!-- Error State -->
    <!-- <div v-if="error" class="error-message">
      {{ error }}
    </div> -->
    <!-- Loading State -->
    <div v-if="loading" class="loading-message">
      Loading machine details...
    </div>
    <!-- Data State -->
    <div v-else-if="machine" class="content">
      <!-- Top Section -->
      <div class="top-section">
        <img :src="machineImage" alt="Machine Image" class="machine-image" />
        <div class="info-panel">
          <p><strong>ID:</strong> {{ machine.id }}</p>
          <p><strong>Name:</strong> {{ machine.name }}</p>
          <p><strong>Status:</strong> <span :class="['status', machine.status]">{{ machine.status }}</span></p>
          <p><strong>Factory:</strong> {{ machine.factory }}</p>
          <p><strong>Area:</strong> {{ machine.area }}</p>
          <p><strong>OEM Code:</strong> {{ machine.oem_code || 'N/A' }}</p>
        </div>
      </div>

      <!-- Table Section -->
      <div class="table-section">
        <h3 class="table-title">Downtime Reasons</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Created At</th>
              <th>Start Time</th>
              <th>Duration</th>
              <th>Status</th>
              <th>Reason</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in visibleTableData" :key="index">
              <td>{{ entry.name }}</td>
              <td>{{ entry.created_date }}</td>
              <td>{{ entry.start_date_time || 'N/A' }}</td>
              <td>{{ entry.duration }}</td>
              <td>
                <span :class="['status', entry.status === 'Open' ? 'stopped' : 'running']">
                  {{ entry.status }}
                </span>
              </td>              
              <td>{{ entry.reaon || 'N/A' }}</td>
              <td>
                <button
                  class="action-btn"
                  :disabled="entry.status === 'Closed'"
                  :style="entry.status === 'Closed' ? 'opacity:0.5;cursor:not-allowed;' : ''"
                  @click="openUpdateDialog(entry)"
                >
                  Update Reason
                </button>
              </td>
            </tr>
            <tr class="load-more" v-if="visibleCount < tableData.length">
              <td colspan="7">
                <button class="load-more-btn" @click="loadMore">Load More</button>
              </td>
            </tr>
            <tr v-if="tableData.length === 0">
              <td colspan="7">No downtime records found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <!-- No Data State -->
    <div v-else class="no-data-message">
      Machine not found.
    </div>

    <!-- Update Reason Dialog -->
    <UpdateReasonDialog
      :visible="showUpdateDialog"
      :downtimeId="selectedDowntime?.name"
      @update="handleReasonUpdate"
      @cancel="closeUpdateDialog"
    />

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createDocumentResource, createListResource } from 'frappe-ui';
import machineImage from '../assets/image.png';
import UpdateReasonDialog from './UpdateReasonDialog.vue';
import { checkRunningStatus } from '../utils/machineStatus'; 

// Router setup
const route = useRoute();
const machineId = computed(() => route.params.id);

const showUpdateDialog = ref(false);
const selectedDowntime = ref(null);


// Reactive state
const error = ref(null);
const machine = ref(null); // ✅ Fixed: Uncommented this line
const tableData = ref([]);
const loading = ref(false);

const visibleCount = ref(4);
const visibleTableData = computed(() => {
  return tableData.value.slice(0, visibleCount.value);
});

const loadMore = () => {
  visibleCount.value += 4;
};

const openUpdateDialog = (entry) => {
  selectedDowntime.value = entry;
  showUpdateDialog.value = true;
};

const closeUpdateDialog = () => {
  showUpdateDialog.value = false;
  selectedDowntime.value = null;
};

// ✅ Fixed: Proper resource initialization and data fetching
watch(
  () => machineId.value,
  async (newId) => {
    if (!newId) {
      error.value = 'No machine ID provided in the URL.';
      return;
    }
    // console.log('Fetching details for machine ID:', newId);
    // Reset state
    error.value = null;
    machine.value = null; // ✅ Fixed: Uncommented this line
    tableData.value = [];
    loading.value = true;

    try {
      // Create machine resource with the actual machine ID
      const machineResource = createDocumentResource({
        doctype: 'Machine',
        name: newId, // Use the actual string value, not computed
        auto: false,
      });

      // console.log('Machine resource created:', machineResource);

      // ✅ Fixed: Proper downtime resource configuration
      const downtimeResource = createListResource({
        doctype: 'Downtime Log',
        //  machine: newId,
        fields: ['name','created_date', 'start_date_time', 'end_date_time', 'duration', 'status', 'reaon'],
        filters: {
          machine: newId
        },
        // orderBy: 'created_date desc',
        // Use the actual string value, not computed
        auto: true,
      });

      // const downtimereason = createListResource({
      //   doctype: 'Downtime Reason',
      //   auto: true,
      // });


      
      // ✅ Fixed: Actually reload the machine resource
      await machineResource.reload();
      
      if (machineResource.doc) {
        // console.log('Machine doc found:', machineResource.doc);
        
        // ✅ Fixed: Assign to the reactive machine ref, not a local variable
        machine.value = {
          id: machineResource.doc.machine_name,
          name: machineResource.doc.machine_name,
          status: await checkRunningStatus(newId),
          factory: machineResource.doc.factory,
          area: machineResource.doc.area,
          oem_code: machineResource.doc.oem_code,
        };

        // console.log('Machine value set:', machine.value);

        // console.log('Downtime reason resource created:', downtimereason);


        // Fetch downtime logs after machine is loaded
        await downtimeResource.reload();
        // console.log('Downtime resource created:', downtimeResource);
        if (downtimeResource.data) {
          tableData.value = downtimeResource.data;
          console.log('Table data set:', tableData.value);
        }
      } else {
        console.log('No machine doc found');
        error.value = 'Machine not found.';
      }
    } catch (err) {
      error.value = `Failed to fetch machine details: ${err.message}`;
      console.error('Error fetching machine details:', err);
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);


const handleReasonUpdate = ({ downtimeId, reason }) => {
  // Update local table data
  const index = tableData.value.findIndex((entry) => entry.name === downtimeId);
  if (index !== -1) {
    tableData.value[index].reason = reason;
  }
  closeUpdateDialog();
};


</script>

<style scoped>
.machine-details-container {
  padding: 24px;
  font-family: 'Segoe UI', sans-serif;
  max-height: 100vh;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #2c3e50;
}

.error-message,
.loading-message,
.no-data-message {
  text-align: center;
  padding: 20px;
  font-size: 16px;
}

.error-message {
  color: #e74c3c;
  background-color: #ffe0e0;
  border-radius: 8px;
}

.loading-message {
  color: #666;
}

.no-data-message {
  color: #666;
}

.top-section {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.machine-image {
  width: 300px;
  height: 200px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.info-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  flex-grow: 1;
}

.status {
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: bold;
  text-transform: capitalize;
}

.status.running {
  background-color: #e0ffe5;
  color: #2ecc71;
}

.status.stopped {
  background-color: #ffe0e0;
  color: #e74c3c;
}

.status.maintenance {
  background-color: #fff6e0;
  color: #f39c12;
}

.table-section {
  margin-top: 30px;
  overflow-y: auto;
}

.table-title {
  margin-bottom: 12px;
  font-size: 18px;
  font-weight: 500;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

thead {
  background-color: #f0f0f0;
}

th, td {
  padding: 12px 16px;
  text-align: left;
}

tbody tr:not(.load-more):hover {
  background-color: #f9f9f9;
}

.load-more {
  text-align: center;
}

.load-more-btn {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.load-more-btn:hover {
  background-color: #2980b9;
}

.action-btn {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.action-btn:hover {
  background-color: #27ae60;
}
</style>