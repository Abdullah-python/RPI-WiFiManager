function submitForm() {
    const = require('fetch');
            
    const ssid = document.getElementById('ssid').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value; 
           
    const data = { ssid, password, email };
            
    fetch('http://wolfpak.portal:3000/wifi-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        })
            .then ((response) => {
                console.log(response.data);
                alert('Creds saved');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            })
            .catch((error) => {
                console.log(error);
                alert('ERROR');
            });
}    


