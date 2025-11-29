import Swal from "sweetalert2";
import { CaptainDetails} from "../interfaces";

export const useCaptainModal = (
    captains: CaptainDetails[],
    vessel: any,
    api: any,
    setCurrentCaptainVessel: (captain: CaptainDetails | null) => void
) => {

    const modalCaptain = async () => {
        const { value: captainName } = await Swal.fire({
            title: "Assign a Captain",
            html: `
                <div class="flex flex-col items-start space-y-3 text-left">
                    <input 
                        id="captainInput" 
                        type="text" 
                        class="input input-bordered w-full text-base-content" 
                        placeholder="Enter or select a captain name"
                    />

                    <div class="divider my-2">Or select from existing captains</div>

                    <div id="captainList" class="flex flex-wrap gap-2">
                        ${captains
                .map(
                    (c) => `
                                <button 
                                    type="button" 
                                    class="btn btn-sm btn-outline hover:btn-primary select-captain"
                                    data-name="${c.username}">
                                    ${c.username}
                                </button>
                            `
                )
                .join("")}
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: "Assign",
            cancelButtonText: "Cancel",
            didOpen: () => {
                const popup = Swal.getPopup();
                const input = popup?.querySelector<HTMLInputElement>("#captainInput");
                const buttons = popup?.querySelectorAll<HTMLButtonElement>(".select-captain");

                buttons?.forEach((btn) => {
                    btn.addEventListener("click", () => {
                        input!.value = btn.getAttribute("data-name") || "";
                    });
                });
            },
            preConfirm: () => {
                const input = Swal.getPopup()!.querySelector<HTMLInputElement>("#captainInput");
                if (!input?.value.trim()) {
                    Swal.showValidationMessage("Please enter or select a captain name!");
                    return false;
                }
                return input.value;
            },
        });

        if (!captainName) return;

        const selectedCaptain = captains.find(c => c.username === captainName);
        if (!selectedCaptain) {
            Swal.fire("Error", "This captain does not exist", "error");
            return;
        }

        await Swal.fire({
            title: "Captain Assigned!",
            text: `This vessel is now assigned to Captain ${captainName}.`,
            icon: "success",
        });

        await api(`/api/v1/vessels/related`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                userId: selectedCaptain.id,
                vesselId: vessel?.id,
            }),
        });

        setCurrentCaptainVessel(selectedCaptain);
    };

    return { modalCaptain };
};
