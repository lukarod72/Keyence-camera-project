// Select the photo card elements
var photoCards = document.querySelectorAll('.photo-card');
        
// Check if the photo card elements exist
if (photoCards.length !== 2) {
    console.log("ERROR: photo cards do not exist. Please check the HTML structure.");
}


function change_photo(photo_1_array, photo_2_array) {
    //each photo array contains: [Photo-Filename, timestamp, program#]
    //example: ["ID:00003-Program_0.jpeg", "15:40:15", "Program_0/"]
    console.log("Photo change requested");

    //had a problem sending a 2D array through socket. We opted to send each column through socket indivudally, then make it a 2D array in JS (here)
    console.log(photo_1_array);//photo one is the newest photo
    console.log(photo_2_array);//photo two is the prevvously newest photo
    var photo_file_list = [photo_1_array, photo_2_array];



    /*explanation of the following loop: earlier we has a problem loading the image in sync with the loop becuase the fetch(url) function is async,
    meaning the loop iteration happens at of sync (quicker) than the fetch statment, making the new image only load into photo container number 2. 
    to fix this issue, we made a function containing everything in the loop, then called it within the loop, ensuring each loop iteration waits 
    for the fetch statement to be complete.*/
    for (var i = 0; i < photoCards.length; i++) {


        (function(index) { // Create a closure or IIFE to capture the value of i
            var imgElement = photoCards[index].querySelector('img');
            var paraElement = photoCards[index].querySelector('p');
            var photoFilename = photo_file_list[index][0];//filename
            var url = '/photos/'+ photo_file_list[index][2]+encodeURIComponent(photoFilename);//path

            fetch(url)
            .then(function(response) {
                return response.blob();
            })
            .then(function(photoBlob) {
                var photoSrc = URL.createObjectURL(photoBlob);
                imgElement.src = photoSrc;
            })
            .catch(function(error) {
                console.log('Error:', error);
            });

            imgElement.alt = photo_file_list[index][1];
            paraElement.textContent = photoFilename;
        })(i); // Pass the value of i as an argument to the closure or IIFE
    }
}


function loadVariable() {
    console.log("Requesting From Server...");
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/get_variable', true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);//contains two tuples, one for each photo
            if(response.Photos_0 == 1){
                //do nothing
                console.log("No updates");
                return 0;
            }
            console.log("Updates...");
            console.log(response);
            change_photo(response.Photos_0, response.Photos_1);
            //document.getElementById('variable-container').innerText = response.variable;
        }
    };
    xhr.send();
}

// Load the variable on page load
window.onload = function () {
    loadVariable(); // Load initially
    setInterval(loadVariable, 4000); // Poll every 2 seconds (adjust the interval as needed)
};
// Emit an event to request the latest photos
//socket.emit('get_latest_photos');