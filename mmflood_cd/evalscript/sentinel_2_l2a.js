function setup() {
    return {
      input: [{
        bands: ["B03", "B12", "SCL"],
      }],
      output: {
        id: "default",
        bands: 2,
        sampleType: SampleType.INT16 //floating point values are automatically rounded to the nearest integer by the service.
      }
    }
  }
  
  function evaluatePixel(sample) {
    let ndvi = (sample.B03 - sample.B12) / (sample.B03 + sample.B12)
    // Return NDVI multiplied by 10000 as integers to save processing units. To obtain NDVI values, simply divide the resulting pixel values by 10000.
    return [ndvi * 10000, sample.SCL]
  }