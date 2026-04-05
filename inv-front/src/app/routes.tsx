import React from 'react';
import { createBrowserRouter, Navigate } from "react-router";
import { Login } from "./components/Login";
import { WarehouseSelect } from "./components/WarehouseSelect";
import { InventorySearch } from "./components/InventorySearch";
import { AdminDashboard } from "./components/AdminDashboard";
import { Reports } from "./components/Reports";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Login,
  },
  {
    path: "/select-warehouse",
    Component: WarehouseSelect,
  },
  {
    path: "/inventory",
    Component: InventorySearch,
  },
  {
    path: "/reports",
    Component: Reports,
  },
  {
    path: "/admin",
    Component: AdminDashboard,
  },
  {
    path: "*",
    Component: () => <Navigate to="/" replace />
  }
]);
