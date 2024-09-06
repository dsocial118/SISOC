


    $(function () {
        // Obtener el objeto JSON desde la variable de contexto 'datos_json'
         

        // Validar si datosJson no es un objeto JSON vacío
        if (Object.keys(datosJson).length > 0) {
            var areaChartData = {
                labels: datosJson.meses,
                datasets: [
                    {
                        label: 'Riesgo familiar',
                        //backgroundColor: 'rgba(60,141,188,0.9)',
                        fill: false,
                        borderColor: 'fuchsia',
                        data: datosJson.Familia
                    },
                    {
                        label: 'Riesgo habitacional',
                        //backgroundColor: 'rgba(210, 214, 222, 1)',
                        fill: false,
                        borderColor: 'lime',
                        data: datosJson.Vivienda
                    },
                    {
                        label: 'Riesgo Salud',
                        //backgroundColor: 'rgba(210, 214, 222, 1)',
                        fill: false,
                        borderColor: 'red',
                        data: datosJson.Salud
                    },
                    {
                        label: 'Riesgo económico',
                        //backgroundColor: 'rgba(210, 214, 222, 1)',
                        fill: false,
                        borderColor: 'blue',
                        data: datosJson.Econom\u00eda
                    },
                    {
                        label: 'Riesgo educacional',
                        //backgroundColor: 'rgba(210, 214, 222, 1)',
                        fill: false,
                        borderColor: 'orange',
                        data: datosJson.Educaci\u00f3n
                    },
                    {
                        label: 'Riesgo laboral',
                        //backgroundColor: 'rgba(210, 214, 222, 1)',
                        fill: false,
                        borderColor: 'gray',
                        data: datosJson.Trabajo
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

            
            var lineChartCanvas = $('#lineChart').get(0).getContext('2d')
            var lineChartOptions = $.extend(true, {}, areaChartOptions)
            var lineChartData = $.extend(true, {}, areaChartData)
            lineChartData.datasets[0].fill = false;
            lineChartData.datasets[1].fill = false;
            lineChartOptions.datasetFill = false

            var lineChart = new Chart(lineChartCanvas, {
                type: 'line',
                data: lineChartData,
                options: lineChartOptions
            });
        };
    });