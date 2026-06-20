import a1Mock from "@/data/mock/a1.json";
import a2Mock from "@/data/mock/a2.json";
import a3Mock from "@/data/mock/a3.json";
import a4Mock from "@/data/mock/a4.json";
import a5Mock from "@/data/mock/a5.json";
import a6Mock from "@/data/mock/a6.json";
import type { A1Data, A2Data, A3Data, A4Data, A5Data, A6Data } from "@/types/agents";

export function getA1Data(): A1Data {
  return a1Mock as A1Data;
}

export function getA2Data(): A2Data {
  return a2Mock as A2Data;
}

export function getA3Data(): A3Data {
  return a3Mock as A3Data;
}

export function getA4Data(): A4Data {
  return a4Mock as A4Data;
}

export function getA5Data(): A5Data {
  return a5Mock as A5Data;
}

export function getA6Data(): A6Data {
  return a6Mock as A6Data;
}
