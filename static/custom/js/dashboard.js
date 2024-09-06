$(function () {
    var areaChartData = {
        labels: ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO'],
        datasets: [
            {
                label: 'Riesgo Hogar',
                backgroundColor: 'rgba(60,141,188,0.5)',
                fill: true,
                borderColor: '#14afe4 ',
                data: [28, 32, 36, 24, 31, 30, 25, 18]
            },
            {
                label: 'Riesgo Educacion',
                backgroundColor: 'rgba(210, 214, 222, 0.5)',
                fill: true,
                borderColor: '#5d5d5d ',
                data: [32, 28, 30, 29, 25, 22, 28, 12]
            },
        ]
    }

    var areaChartOptions = {
        maintainAspectRatio: false,
        responsive: true,
        legend: {
            display: false
        },
        scales: {
            xAxes: [{
                gridLines: {
                    display: true,
                }
            }],
            yAxes: [{
                gridLines: {
                    display: true,
                }
            }]
        }
    }
    var ctx = $('#areaChart').get(0).getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: areaChartData,
        options: areaChartOptions
    });
    
});