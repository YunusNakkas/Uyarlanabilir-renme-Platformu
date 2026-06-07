const { spawn } = require('child_process');

const predictLearningPath = (studentData) => {
    const pythonProcess = spawn('python', ['ml_model.py', JSON.stringify(studentData)]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Önerilen Yol: ${data.toString()}`);
    });
};