// टैब बदलने के लिए फ़ंक्शन
function showTab(tabId, element) {
    document.querySelectorAll('.filter-section').forEach(section => {
        section.classList.add('hidden');
        section.classList.remove('active');
    });
    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById(tabId).classList.add('active');

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    element.classList.add('active');
}

// फ़िल्टर चलाने के लिए मुख्य फ़ंक्शन
async function runFilter(filterType) {
    let resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '<p class="text-center text-blue-600 font-medium animate-pulse">फ़िल्टर चल रहा है... कृपया प्रतीक्षा करें।</p>';

    try {
        // यहाँ fetch URL आपके डोमेन पर /api/filter पर पॉइंट करता है
        const response = await fetch(`/api/filter?type=${filterType}`);

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const results = await response.json();
        
        displayResults(results);

    } catch (error) {
        console.error("बैकएंड से डेटा लाने में त्रुटि हुई:", error);
        resultsList.innerHTML = '<p class="text-center text-red-500">डेटा लाने में त्रुटि हुई। कृपया सुनिश्चित करें कि आपका Python बैकएंड Vercel पर सही से चल रहा है।</p>';
    }
}

// परिणामों को UI में दिखाने के लिए फ़ंक्शन
function displayResults(results) {
    let resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';
    
    if (results.length > 0) {
        results.forEach(stock => {
            let listItem = document.createElement('div');
            listItem.className = 'bg-white p-4 mb-3 rounded-lg shadow-sm border border-gray-200 text-lg font-medium';
            listItem.textContent = stock;
            resultsList.appendChild(listItem);
        });
    } else {
        resultsList.innerHTML = '<p class="text-center text-gray-500 italic">इस फ़िल्टर के लिए कोई स्टॉक नहीं मिला।</p>';
    }
}
