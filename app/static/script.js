document.addEventListener('DOMContentLoaded', function() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            fetch(`/api/current_weather?lat=${lat}&lon=${lon}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('weather-output').innerText = data.error;
                    } else {
                        document.getElementById('weather-output').innerHTML = `
                            <p>City: ${data.name}</p>
                            <p>Country: ${data.sys.country}</p>
                            <p>Temperature: ${data.main.temp} °C</p>
                            <p>Description: ${data.weather[0].description}</p>
                        `;
                    }
                })
                .catch(error => console.error('Error:', error));
        }, function(error) {
            console.error('Geolocation error:', error);
        });
    } else {
        console.error('Geolocation is not supported by this browser.');
    }
});

document.getElementById('weather-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const city = document.getElementById('city').value;
    fetch(`/api/current_weather?location=${encodeURIComponent(city)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('weather-output').innerText = data.error;
            } else {
                document.getElementById('weather-output').innerHTML = `
                    <p>City: ${data.name}</p>
                    <p>Country: ${data.sys.country}</p>
                    <p>Temperature: ${data.main.temp} °C</p>
                    <p>Description: ${data.weather[0].description}</p>
                `;
            }
        })
        .catch(error => console.error('Error:', error));
});
