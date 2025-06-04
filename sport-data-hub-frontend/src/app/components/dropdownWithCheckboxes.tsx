import { useState, useEffect} from "react";

const DropdownCheckboxes: React.FC<{ options: string[]; setSelectedOptions: (options: string[]) => void }> = ({ options, setSelectedOptions}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOptions, setLocalSelectedOptions] = useState<string[]>([]);
  const [areAllChecked, setAreAllChecked] = useState(false);

  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setLocalSelectedOptions(prev =>
      prev.includes(value) ? prev.filter(opt => opt !== value) : [...prev, value]
    );
    setSelectedOptions(selectedOptions);
  };

  useEffect(() => {
    setSelectedOptions(selectedOptions); // Ensures latest update is passed
  }, [selectedOptions]);

  const handleCheckAll = () => {
    if (areAllChecked) {
      setLocalSelectedOptions([]);
    } else {
      setLocalSelectedOptions([...options]);
    }
    setAreAllChecked(!areAllChecked);
  };

  return (
    <div className="relative inline-block text-sm text-gray-800 min-w-xs">
      {/* Label for dropdown */}
      <label
        onClick={() => setIsOpen(!isOpen)}
        className="block bg-blue-600 px-4 py-2 cursor-pointer rounded-md flex justify-between items-center"
      >
        {selectedOptions.length === 0
          ? "Select Options"
          : selectedOptions.length === options.length
          ? "All Selected"
          : `${selectedOptions.length} Selected`}
        <span>{isOpen ? "▲" : "▼"}</span>
      </label>

      {isOpen && (
        <div className="absolute left-0 right-0 mt-2 bg-white border border-gray-300 shadow-lg p-3 max-h-[66vh] overflow-y-auto">
          {/* Check all button */}
          <a
            onClick={handleCheckAll}
            className="block cursor-pointer text-green-600 hover:underline mb-2"
          >
            {areAllChecked ? "Uncheck All" : "Check All"}
          </a>

          {/* Checkbox options */}
          {options.map(option => (
            <label key={option} className="block px-2 py-1">
              <input
                type="checkbox"
                value={option}
                checked={selectedOptions.includes(option)}
                onChange={handleCheckboxChange}
                className="mr-2"
              />
              {option}
            </label>
          ))}
        </div>
      )}
    </div>
  );
};

export default DropdownCheckboxes;
