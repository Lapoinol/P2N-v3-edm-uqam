
const FusionList = ({ fusion_list }) => (
    <div className="mt-4 p-4 border border-gray-200 rounded">
        <div className="flex flex-row justify-between items-center">
            <p className="font-semibold mr-3">
                { (!fusion_list.start && !fusion_list.end) && "La fusion des données va commencer" }
                { (fusion_list.start && !fusion_list.end) && "Les données sont en cours de fusion" }
                { (fusion_list.end) && "La fusion des données est terminé" }
            </p>
            { !fusion_list.end && (
                <svg className="animate-spin -ml-1 h-5 w-5 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            )}
        </div>
    </div>
)

export default FusionList