/** @odoo-module **/

/**
 * Dashboard Analytics Component untuk yhc_employee_export
 * 
 * Komponen OWL yang menampilkan dashboard analytics karyawan
 * dengan berbagai grafik dan KPI cards menggunakan Chart.js.
 */

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class HrEmployeeDashboard extends Component {
    static template = "yhc_employee_export.Dashboard";
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        
        // State untuk menyimpan data dashboard
        this.state = useState({
            loading: true,
            error: null,
            // KPI Data
            kpiData: {
                totalEmployees: 0,
                activeEmployees: 0,
                inactiveEmployees: 0,
                avgAge: 0,
                avgTenure: 0,
                newHiresThisMonth: 0,
                resignsThisMonth: 0,
                maleCount: 0,
                femaleCount: 0,
            },
            // Chart Data
            genderData: { male: 0, female: 0 },
            ageData: {},
            departmentData: {},
            educationData: {},
            employmentTypeData: {},
            serviceLengthData: {},
            bpjsData: {
                kesehatan: { registered: 0, not_registered: 0 },
                ketenagakerjaan: { registered: 0, not_registered: 0 },
            },
            religionData: {},
            maritalData: {},
            // Filter
            selectedDepartment: false,
            selectedYear: new Date().getFullYear(),
            departments: [],
        });
        
        // Chart instances
        this.charts = {};
        
        // Refs untuk canvas charts
        this.genderChartRef = useRef("genderChart");
        this.ageChartRef = useRef("ageChart");
        this.departmentChartRef = useRef("departmentChart");
        this.educationChartRef = useRef("educationChart");
        this.employmentTypeChartRef = useRef("employmentTypeChart");
        this.serviceLengthChartRef = useRef("serviceLengthChart");
        this.bpjsChartRef = useRef("bpjsChart");
        this.religionChartRef = useRef("religionChart");
        
        // Load Chart.js dan data
        onWillStart(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js");
            await this.loadDepartments();
            await this.loadDashboardData();
        });
        
        onMounted(() => {
            this.renderAllCharts();
        });
        
        onWillUnmount(() => {
            this.destroyAllCharts();
        });
    }
    
    /**
     * Load list departments untuk filter
     */
    async loadDepartments() {
        try {
            const departments = await this.orm.searchRead(
                "hr.department",
                [],
                ["id", "name"],
                { order: "name" }
            );
            this.state.departments = departments;
        } catch (error) {
            console.error("Error loading departments:", error);
        }
    }
    
    /**
     * Memuat data dashboard dari backend
     */
    async loadDashboardData() {
        try {
            this.state.loading = true;
            this.state.error = null;
            
            // Call backend method
            const data = await this.orm.call(
                "hr.employee.analytics",
                "get_dashboard_data",
                [],
                { department_id: this.state.selectedDepartment }
            );
            
            if (data) {
                // Update KPI data
                this.state.kpiData = data.kpi || this.state.kpiData;
                
                // Update chart data
                this.state.genderData = data.gender || this.state.genderData;
                this.state.ageData = data.age_groups || this.state.ageData;
                this.state.departmentData = data.departments || this.state.departmentData;
                this.state.educationData = data.education || this.state.educationData;
                this.state.employmentTypeData = data.employment_type || this.state.employmentTypeData;
                this.state.serviceLengthData = data.service_length || this.state.serviceLengthData;
                this.state.bpjsData = data.bpjs || this.state.bpjsData;
                this.state.religionData = data.religion || this.state.religionData;
                this.state.maritalData = data.marital || this.state.maritalData;
            }
            
            this.state.loading = false;
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.error = "Gagal memuat data dashboard";
            this.state.loading = false;
            this.notification.add(
                "Gagal memuat data dashboard. Silakan coba lagi.",
                { type: "danger" }
            );
        }
    }
    
    /**
     * Destroy semua chart instances
     */
    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
    
    /**
     * Render semua charts
     */
    renderAllCharts() {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded yet');
            return;
        }
        
        this.destroyAllCharts();
        
        this.renderGenderChart();
        this.renderAgeChart();
        this.renderDepartmentChart();
        this.renderEducationChart();
        this.renderEmploymentTypeChart();
        this.renderServiceLengthChart();
        this.renderBpjsChart();
        this.renderReligionChart();
    }
    
    /**
     * Chart: Gender Distribution (Doughnut)
     */
    renderGenderChart() {
        const canvas = this.genderChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.genderData;
        
        this.charts.gender = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Laki-laki', 'Perempuan'],
                datasets: [{
                    data: [data.male || 0, data.female || 0],
                    backgroundColor: ['#4285F4', '#EA4335'],
                    borderWidth: 2,
                    borderColor: '#ffffff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 15, usePointStyle: true }
                    },
                    title: {
                        display: true,
                        text: 'Distribusi Gender',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });
    }
    
    /**
     * Chart: Age Distribution (Bar)
     */
    renderAgeChart() {
        const canvas = this.ageChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.ageData;
        
        this.charts.age = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: 'Jumlah Karyawan',
                    data: Object.values(data),
                    backgroundColor: '#714B67',
                    borderRadius: 5,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Distribusi Usia',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
    
    /**
     * Chart: Department Distribution (Horizontal Bar)
     */
    renderDepartmentChart() {
        const canvas = this.departmentChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.departmentData;
        
        // Sort by value and take top 10
        const sorted = Object.entries(data)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        this.charts.department = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sorted.map(([label]) => label),
                datasets: [{
                    label: 'Jumlah Karyawan',
                    data: sorted.map(([, value]) => value),
                    backgroundColor: '#00A65A',
                    borderRadius: 5,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Karyawan per Departemen (Top 10)',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    x: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
    
    /**
     * Chart: Education Distribution (Pie)
     */
    renderEducationChart() {
        const canvas = this.educationChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.educationData;
        
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#C9CBCF', '#7C4DFF'
        ];
        
        this.charts.education = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: colors.slice(0, Object.keys(data).length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 10, usePointStyle: true, font: { size: 10 } }
                    },
                    title: {
                        display: true,
                        text: 'Tingkat Pendidikan',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });
    }
    
    /**
     * Chart: Employment Type (Doughnut)
     */
    renderEmploymentTypeChart() {
        const canvas = this.employmentTypeChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.employmentTypeData;
        
        const colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#607D8B'];
        
        this.charts.employmentType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: colors.slice(0, Object.keys(data).length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 10, usePointStyle: true }
                    },
                    title: {
                        display: true,
                        text: 'Tipe Karyawan',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });
    }
    
    /**
     * Chart: Service Length (Bar)
     */
    renderServiceLengthChart() {
        const canvas = this.serviceLengthChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.serviceLengthData;
        
        this.charts.serviceLength = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: 'Jumlah Karyawan',
                    data: Object.values(data),
                    backgroundColor: '#1565C0',
                    borderRadius: 5,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Masa Kerja',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
    
    /**
     * Chart: BPJS Status (Stacked Bar)
     */
    renderBpjsChart() {
        const canvas = this.bpjsChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.bpjsData;
        
        this.charts.bpjs = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['BPJS Kesehatan', 'BPJS Ketenagakerjaan'],
                datasets: [
                    {
                        label: 'Terdaftar',
                        data: [
                            data.kesehatan?.registered || 0,
                            data.ketenagakerjaan?.registered || 0
                        ],
                        backgroundColor: '#4CAF50',
                        borderRadius: 5,
                    },
                    {
                        label: 'Belum Terdaftar',
                        data: [
                            data.kesehatan?.not_registered || 0,
                            data.ketenagakerjaan?.not_registered || 0
                        ],
                        backgroundColor: '#F44336',
                        borderRadius: 5,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 10, usePointStyle: true }
                    },
                    title: {
                        display: true,
                        text: 'Status BPJS',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    x: { stacked: false },
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
    
    /**
     * Chart: Religion Distribution (Pie)
     */
    renderReligionChart() {
        const canvas = this.religionChartRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const data = this.state.religionData;
        
        const colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#00BCD4', '#795548'];
        
        this.charts.religion = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: colors.slice(0, Object.keys(data).length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 10, usePointStyle: true, font: { size: 10 } }
                    },
                    title: {
                        display: true,
                        text: 'Distribusi Agama',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });
    }
    
    // ===== Action Handlers =====
    
    /**
     * Handler untuk refresh data
     */
    async onRefresh() {
        await this.loadDashboardData();
        this.renderAllCharts();
        this.notification.add("Data dashboard berhasil diperbarui", { type: "success" });
    }
    
    /**
     * Handler untuk export dashboard
     */
    async onExportDashboard() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Export Data Karyawan',
            res_model: 'hr.employee.export.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
    
    /**
     * Handler untuk buka list karyawan
     */
    onViewEmployees() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Karyawan',
            res_model: 'hr.employee',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    /**
     * Handler untuk filter berdasarkan departemen
     */
    async onDepartmentChange(ev) {
        this.state.selectedDepartment = ev.target.value ? parseInt(ev.target.value) : false;
        await this.loadDashboardData();
        this.renderAllCharts();
    }
    
    /**
     * Get percentage untuk KPI
     */
    getActivePercentage() {
        const total = this.state.kpiData.totalEmployees;
        const active = this.state.kpiData.activeEmployees;
        return total > 0 ? ((active / total) * 100).toFixed(1) : 0;
    }
    
    getGenderRatio() {
        const male = this.state.genderData.male || 0;
        const female = this.state.genderData.female || 0;
        const total = male + female;
        return total > 0 ? `${((male / total) * 100).toFixed(0)}:${((female / total) * 100).toFixed(0)}` : '0:0';
    }
}

// Register sebagai client action
registry.category("actions").add("hr_employee_dashboard", HrEmployeeDashboard);

export default HrEmployeeDashboard;
