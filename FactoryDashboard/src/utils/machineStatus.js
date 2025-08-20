import { createListResource } from 'frappe-ui';

export async function checkRunningStatus(machineId) {
  if (!machineId) {
    throw new Error('Machine ID is required');
  }

  try {
    const telemetryResource = createListResource({
      doctype: 'Telemetry',
      fields: ['data', 'timestamp'],
      filters: {
        machine: machineId,
      },
      order_by: 'timestamp desc',
      limit: 1,
      auto: false, // Manual fetch for control
    });

    // Fetch the latest telemetry record
    await telemetryResource.reload();

    // Check if data exists
    if (!telemetryResource.data || telemetryResource.data.length === 0) {
      throw new Error(`No telemetry data found for machine: ${machineId}`);
    }

    const telemetryRecord = telemetryResource.data[0];
    let telemetryData = telemetryRecord.data;

    // Parse data if it's a string (Frappe JSON fields may return as strings)
    if (typeof telemetryData === 'string') {
      try {
        telemetryData = JSON.parse(telemetryData);
      } catch (parseError) {
        console.error('Failed to parse telemetry data:', telemetryData, parseError);
        throw new Error('Invalid telemetry data format');
      }
    }

    // Ensure data is a valid object
    if (!telemetryData || typeof telemetryData !== 'object') {
      console.error('Invalid telemetry data:', telemetryData);
      throw new Error('Invalid telemetry data format');
    }

    // Get status from telemetry data
    const status = telemetryData.status;

    if (!status) {
      throw new Error('Status field not found in telemetry data');
    }

    // Return true if status is 'running', false otherwise
    if (status.toLowerCase() === 'running') {
      return 'running';
    } else {
      return 'stopped';
    }
  } catch (error) {
    console.error(`Failed to check running status for machine ${machineId}:`, error);
    throw error; // Rethrow to let the caller handle it
  }
}