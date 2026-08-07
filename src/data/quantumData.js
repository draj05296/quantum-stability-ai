import Papa from "papaparse";

import day1 from "./quantum_data_day1.csv?url";
import day2 from "./quantum_data_day2.csv?url";
import day3 from "./quantum_data_day3.csv?url";
import day4 from "./quantum_data_day4.csv?url";
import day5 from "./quantum_data_day5.csv?url";

async function loadCSV(file) {
  const response = await fetch(file);
  const csvText = await response.text();

  return new Promise((resolve) => {
    Papa.parse(csvText, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        resolve(results.data);
      },
    });
  });
}

export async function getAllQuantumData() {
  const data = {
    day1: await loadCSV(day1),
    day2: await loadCSV(day2),
    day3: await loadCSV(day3),
    day4: await loadCSV(day4),
    day5: await loadCSV(day5),
  };

  return data;
}