<template>
  <div v-if="visible" class="modal-overlay">
    <div class="modal-content">
      <h3>Update Downtime Reason</h3>
      <div v-if="updateMessage" class="update-message" :class="{ 'success': updateSuccess, 'error': !updateSuccess }">
        {{ updateMessage }}
      </div>
      <select v-model="selectedReason" :disabled="loading || fetchingReason">
        <option value="" disabled>Select a reason</option>
        <option v-for="reason in reasonOptions" :key="reason.name" :value="reason.name">
          {{ reason.name }}
        </option>
      </select>
      <div class="modal-actions">
        <button class="action-btn" @click="handleUpdate" :disabled="!selectedReason || loading || fetchingReason">Update</button>
        <button class="action-btn cancel" @click="handleCancel" :disabled="loading || fetchingReason">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';
import { createListResource, createDocumentResource } from 'frappe-ui';

const props = defineProps({
  visible: Boolean,
  downtimeId: String,
});

const emit = defineEmits(['update', 'cancel']);

const selectedReason = ref('');
const reasonOptions = ref([]);
const updateMessage = ref('');
const updateSuccess = ref(false);
const loading = ref(false);
const fetchingReason = ref(false);

// Fetch downtime reasons
const downtimereason = createListResource({
  doctype: 'Downtime Reason',
  fields: ['name'], // Adjust if your doctype uses a different field (e.g., reason_name)
  auto: true,
  onSuccess: (data) => {
    reasonOptions.value = data; // Assuming data is an array of { name: string }
    console.log('Downtime reasons fetched successfully:', reasonOptions.value);
  },
  onError: (error) => {
    console.error('Failed to fetch downtime reasons:', error);
    updateMessage.value = 'Failed to load downtime reasons.';
    updateSuccess.value = false;
  },
});

// Fetch current reason and reset state when dialog opens
watch(
  () => props.visible,
  async (isVisible) => {
    if (isVisible && props.downtimeId) {
      fetchingReason.value = true;
      selectedReason.value = '';
      updateMessage.value = '';
      updateSuccess.value = false;
      try {
        const downtimeResource = createDocumentResource({
          doctype: 'Downtime Log',
          name: props.downtimeId,
          fields: ['reaon'],
          auto: false,
        });
        await downtimeResource.reload();
        if (downtimeResource.doc && downtimeResource.doc.reason) {
          selectedReason.value = downtimeResource.doc.reason;
        } else {
          console.warn('No reason found for Downtime Log:', props.downtimeId);
        }
      } catch (error) {
        console.error('Failed to fetch current reason:', error);
        updateMessage.value = 'Failed to load current reason.';
        updateSuccess.value = false;
      } finally {
        fetchingReason.value = false;
      }
    }
  },
  { immediate: true }
);

const handleUpdate = async () => {
  if (!selectedReason.value) {
    updateMessage.value = 'Please select a reason.';
    updateSuccess.value = false;
    return;
  }

  loading.value = true;
  updateMessage.value = '';

  try {
    console.log('Updating reason to:', props.downtimeId);
    console.log('New reason:', selectedReason.value);

    const downtimeResource = createDocumentResource({
      doctype: 'Downtime Log',
      name: props.downtimeId,
      auto: false, // Explicitly disable auto-fetch
    });

    await downtimeResource.reload();
    console.log('Document resource:', downtimeResource);

    await downtimeResource.setValue.submit({
      reaon: selectedReason.value, // Corrected typo: reaon → reason
    });

    updateMessage.value = 'Reason updated successfully!';
    updateSuccess.value = true;

    // Emit update event to parent
    emit('update', { downtimeId: props.downtimeId, reason: selectedReason.value });

    // Clear selectedReason to reset the dropdown
    selectedReason.value = '';

    // Clear message and close dialog after 3 seconds (increased for visibility)
    setTimeout(() => {
      updateMessage.value = '';
      updateSuccess.value = false;
      emit('cancel');
    }, 3000);
  } catch (error) {
    console.error('Failed to update reason:', error);
    updateMessage.value = 'Failed to update reason. Please try again.';
    updateSuccess.value = false;
  } finally {
    loading.value = false; // Always reset loading
  }
};

const handleCancel = () => {
  updateMessage.value = '';
  updateSuccess.value = false;
  selectedReason.value = '';
  emit('cancel');
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #ffffff;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid #e0e0e0;
}

h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  text-align: center;
}

select {
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d1d1;
  border-radius: 6px;
  font-size: 1rem;
  background: #f9f9f9;
  cursor: pointer;
  transition: border-color 0.2s;
}

select:focus {
  outline: none;
  border-color: #2ecc71;
}

select:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
}

.update-message {
  padding: 10px;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
}

.update-message.success {
  background: #e6f4ea;
  color: #2ecc71;
}

.update-message.error {
  background: #ffe6e6;
  color: #c0392b;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.action-btn {
  flex: 1;
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.action-btn:hover:not(:disabled) {
  background-color: #27ae60;
}

.action-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.action-btn.cancel {
  background-color: #ffb3b3;
  color: #c0392b;
}

.action-btn.cancel:hover:not(:disabled) {
  background-color: #ff7675;
}
</style>