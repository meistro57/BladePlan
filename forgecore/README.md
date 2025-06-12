# ForgeCore

ForgeCore is a modular steel fabrication management system designed to run on a LAMP stack with a MySQL backend. All backend logic is written in Python and organized into independent modules. The frontend will be built using PHP/HTML/JS to allow flexible deployment on common web hosting environments.

This repository contains a basic scaffold for the system. Each module comes with a simple CLI harness to demonstrate connectivity to the database and to outline the core responsibilities of the module.

## Directory Layout
```
forgecore/
├── backend/
│   ├── cutlist_optimizer/
│   ├── drawing_parser/
│   ├── inventory_manager/
│   ├── job_tracker/
│   ├── visual_debugger/
│   ├── label_printer/
│   ├── report_engine/
│   └── agent_api/
├── frontend/
│   ├── index.php
│   ├── dashboard/
│   └── mobile_kiosk/
├── database/
│   └── schema.sql
├── config/
│   └── config.py
└── README.md
```

## Getting Started
1. Create a MySQL database and load `database/schema.sql`.
2. Set environment variables `FORGECORE_DB_HOST`, `FORGECORE_DB_USER`, `FORGECORE_DB_PASSWORD`, and `FORGECORE_DB_NAME`.
3. Run module test harnesses using `python backend/<module>/main.py`.

This scaffold is meant as a foundation for future expansion. Each module currently implements a minimal interface for interacting with the database.
