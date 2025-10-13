import React from "react";
import { useNavigate } from "react-router-dom";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import P from "../../components/BaseComponents/P";
import Button from "../../components/BaseComponents/Button";
import FormWrapper from "../../components/BaseComponents/FormWrapper";

const MaritimeExpert = () => {
	const navigate = useNavigate();

	return (
		<div className="min-h-screen bg-gray-100 py-10 flex flex-col items-center">
			<FormWrapper>
				<TitleH1 className="mb-4 text-center">Maritime Expert Area</TitleH1>
				<P className="mb-6 text-center">
					Detailed AIS analytics, vessel technical sheets, and regulation briefs dedicated to maritime experts will appear here.
				</P>
				<Button
					onClick={() => navigate("/")}
					className="w-full px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
				>
					Back to Home
				</Button>
			</FormWrapper>
		</div>
	);
};

export default MaritimeExpert;
